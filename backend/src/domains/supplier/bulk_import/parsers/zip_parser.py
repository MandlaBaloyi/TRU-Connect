"""
Safe ZIP handling -- reads an untrusted, supplier-uploaded ZIP of
product images WITHOUT ever fully extracting it to disk. Everything
here operates on ZipFile's own in-memory index (ZipInfo entries) before
touching any entry's actual bytes, and even then only reads bytes into
memory for entries that pass every check -- never a blind "extract
everything, check later" approach.

THREE DISTINCT ATTACKS THIS DEFENDS AGAINST, EACH WITH ITS OWN CHECK:

1. PATH TRAVERSAL -- an entry named "../../etc/passwd" or an absolute
   path. Guarded by resolving the entry's WOULD-BE destination against
   a real base directory and confirming it's still inside that
   directory (realpath-based containment check), not just by ".." in
   the string (a string check that misses encoded variants,
   Windows-style separators, symlink tricks, etc.).

2. ZIP BOMBS -- a tiny compressed file that expands to gigabytes.
   Guarded on TWO numbers BEFORE extraction: total UNCOMPRESSED size
   across all entries, and each entry's own compression RATIO
   (file_size / compress_size) -- a single entry with an extreme ratio
   is the classic bomb signature even if the total stays under the
   size cap.

3. TOO MANY FILES -- thousands of tiny entries, each individually
   fine, that still add up to a resource-exhaustion problem during
   processing. Guarded by a flat entry-count cap.

Only entries with a recognised image extension are ever read into
memory at all -- this ZIP is "photos for products", not a general file
drop; anything else inside it (a script, an executable, a nested
archive) is skipped, never opened.
"""
from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass
from typing import Dict, List

MAX_TOTAL_UNCOMPRESSED_BYTES = 200 * 1024 * 1024  # 200MB across the whole archive
# HARD TECHNICAL SAFETY CEILING, distinct from any tier's own business
# limit (products/tiers/*.py's own max_image_upload_bytes, currently
# 3-8MB) -- this is purely "how big can a single entry be before we
# refuse to even look at it", set with headroom above Max tier's own
# highest number so the tier check (enforced later, in
# product_media_service.py) is always the one that actually fires for
# a real oversized photo, not this file's own blunter safety net.
MAX_SINGLE_FILE_UNCOMPRESSED_BYTES = 10 * 1024 * 1024
# Same reasoning -- headroom above Max tier's own bulk_max_images_per_job
# (300), so THAT tier check is what normally fires; this is the
# absolute technical ceiling protecting against a genuinely
# pathological archive regardless of any tier.
MAX_ENTRY_COUNT = 350
# A ratio above this for any single entry is the classic zip-bomb
# signature -- a real photo (already-compressed JPEG/PNG data) rarely
# compresses more than ~1.1x further; a ratio this extreme means the
# entry is almost certainly not a real image at all.
MAX_COMPRESSION_RATIO = 100

ALLOWED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


class UnsafeZipError(Exception):
    """Raised for anything this parser refuses to process -- the
    caller (bulk_import's own validator/service) turns this into a
    clear, whole-file-level import error, never a 500.

    is_malicious IS DELIBERATELY FALSE BY DEFAULT, TRUE ONLY AT THE TWO
    RAISE SITES BELOW WHERE THERE IS NO PLAUSIBLE HONEST CAUSE -- path
    traversal and a suspicious compression ratio. Everything else
    (too many files, a single file over the size ceiling, total size
    too large, a corrupted zip) could genuinely happen to an honest
    supplier with a large real catalog or a bad upload -- see
    services/abuse_tracking.py's own docstring for the full reasoning
    on why only these two count toward a lockout."""

    def __init__(self, message: str, is_malicious: bool = False):
        super().__init__(message)
        self.is_malicious = is_malicious


@dataclass(frozen=True)
class ZipImageEntry:
    filename: str  # basename only, folder structure inside the zip is ignored
    uncompressed_size: int


def _is_safe_member_path(base_dir: str, member_name: str) -> bool:
    """True only if extracting `member_name` under `base_dir` could
    never land outside `base_dir` -- resolved as real filesystem paths,
    not string-matched, so this can't be fooled by an encoded or
    platform-specific traversal sequence."""
    target = os.path.realpath(os.path.join(base_dir, member_name))
    base = os.path.realpath(base_dir)
    return target == base or target.startswith(base + os.sep)


def inspect_zip(file_path: str) -> List[ZipImageEntry]:
    """First pass: read ONLY the archive's own index (no bytes
    extracted yet) and validate every safety property. Raises
    UnsafeZipError on the first violation found -- never partially
    proceeds with a suspicious archive."""
    try:
        zf = zipfile.ZipFile(file_path)
    except zipfile.BadZipFile as exc:
        raise UnsafeZipError("This doesn't look like a valid ZIP file.") from exc

    with zf:
        infos = zf.infolist()

        if len(infos) > MAX_ENTRY_COUNT:
            raise UnsafeZipError(f"ZIP contains too many files (max {MAX_ENTRY_COUNT}).")

        total_uncompressed = 0
        entries: List[ZipImageEntry] = []

        for info in infos:
            if info.is_dir():
                continue

            # Path traversal check -- BEFORE anything else touches this
            # entry, using a real filesystem base (a throwaway
            # directory that's never actually written to at this
            # inspect-only stage, just used as the anchor for the
            # realpath check).
            if not _is_safe_member_path("/tmp/tru_connect_zip_sandbox", info.filename):
                raise UnsafeZipError(f"Unsafe file path inside ZIP: {info.filename!r}", is_malicious=True)

            # macOS's own __MACOSX metadata folder and hidden files --
            # never real image content, always skipped, same rule the
            # frontend's own parseImageManifest.ts already applies.
            basename = os.path.basename(info.filename)
            if info.filename.startswith("__MACOSX/") or basename.startswith("."):
                continue

            if not basename.lower().endswith(ALLOWED_IMAGE_EXTENSIONS):
                continue  # not an image -- skipped, never opened

            if info.file_size > MAX_SINGLE_FILE_UNCOMPRESSED_BYTES:
                raise UnsafeZipError(f"{basename} is too large ({info.file_size} bytes).")

            if info.compress_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > MAX_COMPRESSION_RATIO:
                    raise UnsafeZipError(
                        f"{basename} has a suspicious compression ratio -- refusing to extract.", is_malicious=True
                    )

            total_uncompressed += info.file_size
            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
                raise UnsafeZipError("ZIP's total uncompressed size is too large.")

            entries.append(ZipImageEntry(filename=basename, uncompressed_size=info.file_size))

        return entries


def extract_image_bytes(file_path: str, target_filenames: set) -> Dict[str, bytes]:
    """Second pass, called ONLY after inspect_zip has already validated
    the whole archive -- reads bytes into memory for exactly the
    filenames the caller actually needs (the ones referenced by valid
    spreadsheet rows), never the whole archive indiscriminately.
    Matching is by basename, same as inspect_zip's own entries."""
    result: Dict[str, bytes] = {}
    with zipfile.ZipFile(file_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            basename = os.path.basename(info.filename)
            if basename in target_filenames and basename not in result:
                result[basename] = zf.read(info)
    return result
