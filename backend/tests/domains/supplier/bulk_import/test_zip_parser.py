"""
zip_parser tests -- formalizes the direct manual verification already
run against real malicious ZIPs before this file existed.
"""
from __future__ import annotations

import os
import zipfile

import pytest

from src.domains.supplier.bulk_import.parsers.zip_parser import (
    UnsafeZipError,
    extract_image_bytes,
    inspect_zip,
)


def _write_zip(tmp_path, entries: dict, compression=zipfile.ZIP_STORED) -> str:
    path = str(tmp_path / "test.zip")
    with zipfile.ZipFile(path, "w", compression) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return path


class TestPathTraversal:
    def test_rejects_relative_traversal(self, tmp_path):
        path = _write_zip(tmp_path, {"../../../etc/evil.jpg": b"data"})
        with pytest.raises(UnsafeZipError, match="Unsafe file path"):
            inspect_zip(path)

    def test_rejects_absolute_path(self, tmp_path):
        path = _write_zip(tmp_path, {"/etc/evil.jpg": b"data"})
        with pytest.raises(UnsafeZipError, match="Unsafe file path"):
            inspect_zip(path)


class TestZipBomb:
    def test_rejects_oversized_single_entry(self, tmp_path):
        path = _write_zip(tmp_path, {"bomb.jpg": b"0" * 50_000_000}, compression=zipfile.ZIP_DEFLATED)
        with pytest.raises(UnsafeZipError, match="too large"):
            inspect_zip(path)

    def test_rejects_suspicious_compression_ratio_even_under_size_cap(self, tmp_path):
        """A bomb that stays UNDER the single-file size cap (now 10MB,
        tightened during the tier-limits review) but has an extreme
        ratio -- the ratio check must catch this independently of the
        size check."""
        path = _write_zip(tmp_path, {"sneaky.jpg": b"0" * 9_000_000}, compression=zipfile.ZIP_DEFLATED)
        with pytest.raises(UnsafeZipError, match="compression ratio"):
            inspect_zip(path)

    def test_rejects_oversized_total_across_many_entries(self, tmp_path):
        entries = {f"img{i}.jpg": os.urandom(1000) for i in range(50)}
        path = _write_zip(tmp_path, entries)
        from src.domains.supplier.bulk_import.parsers import zip_parser

        original_cap = zip_parser.MAX_TOTAL_UNCOMPRESSED_BYTES
        zip_parser.MAX_TOTAL_UNCOMPRESSED_BYTES = 10_000  # lower than the 50KB this zip contains
        try:
            with pytest.raises(UnsafeZipError, match="total uncompressed size"):
                inspect_zip(path)
        finally:
            zip_parser.MAX_TOTAL_UNCOMPRESSED_BYTES = original_cap


class TestEntryCount:
    def test_rejects_too_many_entries(self, tmp_path):
        entries = {f"img{i}.jpg": b"x" for i in range(700)}
        path = _write_zip(tmp_path, entries)
        with pytest.raises(UnsafeZipError, match="too many files"):
            inspect_zip(path)


class TestSafeZip:
    def test_real_safe_zip_parses_correctly(self, tmp_path):
        path = _write_zip(
            tmp_path,
            {
                "coke500.jpg": b"real jpeg bytes",
                "images/simba120.png": b"real png bytes",
                "__MACOSX/._coke500.jpg": b"mac junk",
                ".hidden": b"hidden junk",
                "notes.txt": b"not an image",
            },
        )

        entries = inspect_zip(path)

        filenames = {e.filename for e in entries}
        assert filenames == {"coke500.jpg", "simba120.png"}

    def test_extract_image_bytes_returns_only_requested_filenames(self, tmp_path):
        path = _write_zip(tmp_path, {"a.jpg": b"AAA", "b.jpg": b"BBB", "c.jpg": b"CCC"})

        result = extract_image_bytes(path, {"a.jpg", "c.jpg"})

        assert result == {"a.jpg": b"AAA", "c.jpg": b"CCC"}


def test_bad_zip_file_raises_clear_error(tmp_path):
    path = str(tmp_path / "notazip.zip")
    with open(path, "wb") as f:
        f.write(b"this is not a zip file at all")

    with pytest.raises(UnsafeZipError, match="valid ZIP"):
        inspect_zip(path)
