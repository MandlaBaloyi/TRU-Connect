#!/usr/bin/env python3
"""
fix_shared_imports.py

Fixes every import statement broken by reorganize_shared.py's file moves —
scans your ENTIRE src/ and tests/ tree and rewrites old dotted import
paths to their new location. You do not need to identify which files are
affected; this script finds all of them automatically.

WHY NO FILE UPLOADS WERE NEEDED FOR THIS: this is a pure, deterministic
text substitution. The exact same (old_path -> new_path) mapping used to
physically move the files is reused here to fix every reference to them,
regardless of which file contains that reference or what else is in it.

RULE APPLIED, for every moved module (e.g. audit.py: shared/ -> shared/audit/):
    from src.shared.audit import X        -> from src.shared.audit.audit import X
    from src.shared import audit          -> from src.shared.audit import audit
    from src.shared import audit, other   -> from src.shared.audit import audit
                                              (other left/handled on its own
                                               merged line if it moved too --
                                               see MULTI-IMPORT NOTE below)
    import src.shared.audit                -> import src.shared.audit.audit
    src.shared.audit.something (rare        -> src.shared.audit.audit.something
        fully-qualified in-code reference)

MULTI-IMPORT NOTE: `from src.shared import audit, audit_context` is a
special case where TWO names on one line both moved into the SAME new
package (src.shared.audit). The script detects this and merges them onto
one corrected line: `from src.shared.audit import audit, audit_context`
rather than producing two separate lines that would each re-import the
same package. If a bare multi-import line mixes names that moved to
DIFFERENT new packages, the script reports it instead of guessing, since
that split cannot be done safely by regex alone.

WHAT THIS SCRIPT DOES NOT TOUCH:
    - .html template files (no Python imports to fix).
    - src/shared/email/email.py's Jinja2/template FOLDER PATH, if it is
      expressed as a string literal (e.g. a hardcoded "shared/templates"
      path) rather than derived relative to the module's own file
      location. That is a file-path string, not an import statement, and
      this script only touches import statements. See the printed
      reminder at the end of a run.
    - src/shared/audit.py.bak (left alone, as agreed during the move).

SAFETY:
    - --dry-run shows every change as a unified diff without writing
      anything.
    - Without --dry-run, each changed file is backed up alongside itself
      as `<file>.importfix.bak` before being overwritten (skip with
      --no-backup once you've reviewed the dry-run output and trust it).
    - Only rewrites files that actually contain a broken pattern; every
      other file is left completely alone.

Usage:
    python fix_shared_imports.py --root . --dry-run
    python fix_shared_imports.py --root .
    python fix_shared_imports.py --root . --no-backup
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

# (old_module_name, new_subpackage) -- derived from the exact same
# mapping reorganize_shared.py used to physically move each file.
# old dotted path is always `src.shared.<old_module_name>`
# new dotted path is always `src.shared.<new_subpackage>.<old_module_name>`
MOVED_MODULES: list[tuple[str, str]] = [
    ("audit", "audit"),
    ("audit_context", "audit"),
    ("audit_types", "audit"),
    ("cache", "cache"),
    ("constants", "constants"),
    ("email", "email"),
    ("helpers", "helpers"),
    ("logger", "logging"),
    ("metrics", "logging"),
    ("monitoring", "monitoring"),
    ("queue", "queue"),
    ("scheduling_types", "scheduling"),
    ("security", "security"),
    ("tickets", "tickets"),
    ("validators", "validation"),
]

OLD_TO_NEW = {old: new for old, new in MOVED_MODULES}

SCAN_DIRS = ["src", "tests"]
FILE_GLOB = "*.py"


def _build_multi_import_pattern() -> re.Pattern:
    # Matches: from src.shared import name1, name2, ...
    # Captures the whole name list so we can inspect/rewrite it.
    return re.compile(r"from\s+src\.shared\s+import\s+([A-Za-z0-9_,\s]+)")


MULTI_IMPORT_RE = _build_multi_import_pattern()


def fix_bare_multi_import(line: str) -> tuple[str, list[str]]:
    """
    Handles `from src.shared import name1, name2, ...` where one or more
    names are modules that moved. Names moving to the SAME new
    subpackage are merged onto one corrected import line. Names moving to
    DIFFERENT subpackages, or names that did NOT move at all (still live
    directly in src/shared/), are reported as warnings rather than guessed.

    Returns (possibly-rewritten line, list of warning strings).
    """
    match = MULTI_IMPORT_RE.search(line)
    if not match:
        return line, []

    names = [n.strip() for n in match.group(1).split(",") if n.strip()]
    moved = [n for n in names if n in OLD_TO_NEW]
    not_moved = [n for n in names if n not in OLD_TO_NEW]

    if not moved:
        return line, []  # nothing here moved; not our concern

    warnings = []
    if not_moved:
        warnings.append(
            f"Line mixes moved and un-moved names, left as-is for manual review: {line.strip()!r} "
            f"(un-moved: {not_moved})"
        )
        return line, warnings

    destinations = {OLD_TO_NEW[n] for n in moved}
    if len(destinations) > 1:
        warnings.append(
            f"Line's names moved to DIFFERENT subpackages, cannot auto-merge, "
            f"needs manual split: {line.strip()!r} (destinations: {destinations})"
        )
        return line, warnings

    dest = destinations.pop()
    prefix_match = re.match(r"^(\s*)", line)
    indent = prefix_match.group(1) if prefix_match else ""
    new_line = f"{indent}from src.shared.{dest} import {', '.join(moved)}\n"
    return new_line, []


def _build_destination_groups() -> dict[str, list[str]]:
    """Maps each new subpackage name to every old module name that moves
    into it -- e.g. "audit" -> ["audit", "audit_context", "audit_types"].
    Used to build guards that stop an already-correct path from being
    matched again on a re-run."""
    groups: dict[str, list[str]] = {}
    for old, new_sub in MOVED_MODULES:
        groups.setdefault(new_sub, []).append(old)
    return groups


DESTINATION_GROUPS = _build_destination_groups()


def _build_qualified_patterns() -> list[tuple[re.Pattern, str]]:
    """
    Builds one guarded regex per moved module. A guard is only needed
    when `old == new_sub` -- that's the only situation where the fixed
    path ("src.shared.<old>.<old>...") still contains the OLD pattern as
    a literal, matchable prefix, since the destination folder happens to
    share the module's original name (audit, cache, constants, email,
    helpers, monitoring, queue, security, tickets all hit this).

    Two guards, for two different already-fixed shapes:
      1. `(?!\\.(?:sibling1|sibling2|...)\\b)` -- blocks re-matching a
         path that's already correctly nested under this folder, e.g.
         "src.shared.audit.audit_types" (audit_types is a SIBLING of
         audit.py in the same audit/ folder, not a re-fixable target).
      2. `(?!\\s+import\\b)` -- audit-SPECIFIC. audit.py is exclusively
         ever imported via the bare `from src.shared import audit` form
         in this codebase (never `from src.shared.audit import
         something`) -- so once the bare-import fixer produces `from
         src.shared.audit import audit, audit_context`, that shape must
         never be treated as still-broken. This guard is intentionally
         NOT applied to the other 8 self-named entries (cache, constants,
         email, helpers, monitoring, queue, security, tickets), because
         THEIR genuinely-broken original form really is
         "from src.shared.<name> import <thing>" -- applying this guard
         there would incorrectly skip fixing them on the very first run.
    """
    patterns = []
    for old, new_sub in MOVED_MODULES:
        guard = ""
        if old == new_sub:
            siblings = DESTINATION_GROUPS[new_sub]
            alternation = "|".join(re.escape(s) for s in siblings)
            guard = rf"(?!\.(?:{alternation})\b)"
            if old == "audit":
                guard += r"(?!\s+import\b)"
        pattern = re.compile(rf"\bsrc\.shared\.{re.escape(old)}\b{guard}")
        patterns.append((pattern, f"src.shared.{new_sub}.{old}"))
    return patterns


QUALIFIED_PATTERNS = _build_qualified_patterns()


def fix_qualified_imports(text: str) -> tuple[str, int]:
    """
    Handles the two common single-target forms:
        from src.shared.<old> import ...
        import src.shared.<old>
        import src.shared.<old> as ...
    and any other in-code fully-qualified reference to src.shared.<old>
    (e.g. a string used in mock.patch("src.shared.audit.log_x")).

    Uses \\b (word boundary) after <old> so e.g. "audit" never matches
    inside "audit_context" or "audit_types" -- underscore is a "word"
    character in regex, so there is no boundary between "audit" and "_",
    meaning this is safe by construction, not by luck.

    IDEMPOTENT: guarded (see _build_qualified_patterns) so re-running this
    script on already-fixed files is a safe no-op rather than progressively
    re-nesting paths that happen to share a name with their destination
    folder.
    """
    count = 0
    for pattern, replacement in QUALIFIED_PATTERNS:
        text, n = pattern.subn(replacement, text)
        count += n
    return text, count


BARE_IMPORT_LINE_RE = re.compile(r"^\s*from\s+src\.shared\s+import\s+")


def fix_file(text: str) -> tuple[str, int, list[str]]:
    """
    Processes the file ONE LINE AT A TIME, dispatching each line to
    exactly one fix path:
      - lines matching `from src.shared import ...` (bare form) go
        through fix_bare_multi_import ONLY.
      - every other line goes through fix_qualified_imports ONLY.

    CRITICAL: a line must never pass through both fixers. An earlier
    version of this script ran the bare-import fix first, then re-ran the
    qualified-import regex over the WHOLE file afterward — which matched
    already-corrected bare-import lines a second time and double-nested
    them (e.g. `from src.shared.audit import audit_context` incorrectly
    became `from src.shared.audit.audit import audit_context`). Dispatching
    per-line instead of per-file-then-per-file eliminates that class of
    bug by construction: each line is touched by exactly one regex pass.
    """
    lines = text.splitlines(keepends=True)
    new_lines = []
    warnings: list[str] = []
    total_fixes = 0

    for line in lines:
        if BARE_IMPORT_LINE_RE.match(line):
            fixed_line, line_warnings = fix_bare_multi_import(line)
            if fixed_line != line:
                total_fixes += 1
            warnings.extend(line_warnings)
            new_lines.append(fixed_line)
        else:
            fixed_line, n = fix_qualified_imports(line)
            total_fixes += n
            new_lines.append(fixed_line)

    return "".join(new_lines), total_fixes, warnings


def iter_python_files(root: Path):
    for scan_dir in SCAN_DIRS:
        base = root / scan_dir
        if not base.exists():
            continue
        for path in base.rglob(FILE_GLOB):
            if path.is_file():
                yield path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", required=True, help="Path to your backend repo root")
    parser.add_argument("--dry-run", action="store_true", help="Show diffs without writing anything")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating .importfix.bak copies")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        print(f"Root path does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    changed_files = []
    all_warnings: list[tuple[str, str]] = []

    for path in iter_python_files(root):
        original = path.read_text(encoding="utf-8")
        fixed, count, warnings = fix_file(original)

        for w in warnings:
            all_warnings.append((str(path.relative_to(root)), w))

        if count == 0:
            continue

        changed_files.append((path, original, fixed, count))

    verb = "Would fix" if args.dry_run else "Fixed"
    print(f"\n{verb} {len(changed_files)} file(s):\n")

    for path, original, fixed, count in changed_files:
        rel = path.relative_to(root)
        print(f"--- {rel} ({count} import reference(s) updated) ---")
        if args.dry_run:
            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                fixed.splitlines(keepends=True),
                fromfile=f"{rel} (before)",
                tofile=f"{rel} (after)",
            )
            sys.stdout.writelines(diff)
            print()
        else:
            if not args.no_backup:
                backup_path = path.with_suffix(path.suffix + ".importfix.bak")
                backup_path.write_text(original, encoding="utf-8")
            path.write_text(fixed, encoding="utf-8")

    if all_warnings:
        print(f"\n{len(all_warnings)} line(s) need MANUAL review (not auto-fixed):")
        for rel, w in all_warnings:
            print(f"  ! {rel}: {w}")

    print(
        "\nNOT covered by this script (check manually):\n"
        "  - src/shared/email/email.py's template FOLDER PATH, if hardcoded\n"
        "    as a string rather than derived from the module's own file\n"
        "    location (e.g. Path(__file__).parent / 'templates'). If it's\n"
        "    file-relative, it likely still resolves correctly since both\n"
        "    email.py and templates/ moved down one level together --\n"
        "    verify, don't assume.\n"
        "  - Any string (not a Python import statement) that references the\n"
        "    old flat path, e.g. in config files, .env, or Flask app_config\n"
        "    template_folder= settings."
    )


if __name__ == "__main__":
    main()