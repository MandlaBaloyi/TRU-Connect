#!/usr/bin/env python3
"""
reorganize_shared.py

Restructures backend/src/shared/ (and the email templates it contains)
from a flat layout into grouped subpackages, to support future growth
(per-domain audit event types, per-domain email templates) without one
folder becoming an unstructured pile of files.

THIS SCRIPT ONLY MOVES FILES. It does not read, parse, or modify the
content of any .py or .html file — every moved file is byte-for-byte
identical at its new path. Import statements inside those files will be
broken after this runs (e.g. audit.py's `from src.shared.audit_context
import ...` needs to become `from src.shared.audit.audit_context import
...`) — fixing those is a deliberate separate pass, not done here.

WHAT MOVES:
    src/shared/audit.py            -> src/shared/audit/audit.py
    src/shared/audit_context.py    -> src/shared/audit/audit_context.py
    src/shared/audit_types.py      -> src/shared/audit/audit_types.py
    src/shared/cache.py            -> src/shared/cache/cache.py
    src/shared/constants.py        -> src/shared/constants/constants.py
    src/shared/email.py            -> src/shared/email/email.py
    src/shared/helpers.py          -> src/shared/helpers/helpers.py
    src/shared/logger.py           -> src/shared/logging/logger.py
    src/shared/metrics.py          -> src/shared/logging/metrics.py
    src/shared/monitoring.py       -> src/shared/monitoring/monitoring.py
    src/shared/queue.py            -> src/shared/queue/queue.py
    src/shared/scheduling_types.py -> src/shared/scheduling/scheduling_types.py
    src/shared/security.py         -> src/shared/security/security.py
    src/shared/tickets.py          -> src/shared/tickets/tickets.py
    src/shared/validators.py       -> src/shared/validation/validators.py

    src/shared/templates/base.html                  -> src/shared/email/templates/base/base.html
    src/shared/templates/otp.html                   -> src/shared/email/templates/auth/otp.html
    src/shared/templates/password_reset.html        -> src/shared/email/templates/auth/password_reset.html
    src/shared/templates/resume_registration.html   -> src/shared/email/templates/auth/resume_registration.html
    src/shared/templates/verification_success.html  -> src/shared/email/templates/auth/verification_success.html
    src/shared/templates/verification_failed.html   -> src/shared/email/templates/auth/verification_failed.html
    src/shared/templates/welcome_business.html       -> src/shared/email/templates/business/welcome_business.html
    src/shared/templates/welcome_supplier.html       -> src/shared/email/templates/supplier/welcome_supplier.html
    src/shared/templates/supplier_invitation.html    -> src/shared/email/templates/supplier/supplier_invitation.html
    src/shared/templates/order_received.html         -> src/shared/email/templates/supplier/order_received.html
    src/shared/templates/order_shipped.html           -> src/shared/email/templates/supplier/order_shipped.html
    src/shared/templates/order_delivered.html         -> src/shared/email/templates/supplier/order_delivered.html

WHAT'S CREATED NEW (empty scaffolding, not moved from anywhere):
    src/shared/audit/event_types/{auth,supplier,business,marketplace,
        verification,trust,security,platform,admin}.py -- placeholder
        files, docstring only. The real AuditEventName enum stays fully
        intact in audit/audit_types.py; nothing is split today.
    src/shared/email/templates/{security,platform,admin}/.gitkeep --
        future template categories, no templates exist yet.
    An __init__.py in every new subpackage.

WHAT'S DELIBERATELY LEFT ALONE:
    src/shared/audit.py.bak -- stays at the old flat location untouched.
    Anything not in the mapping above.

SAFETY:
    - Refuses to overwrite an existing destination file unless --force.
    - Skips (and reports) any source file that doesn't exist, rather than
      failing the whole run -- handles a partially-completed prior run
      gracefully.
    - --dry-run previews every move without touching the filesystem.

Usage:
    python reorganize_shared.py --root .
    python reorganize_shared.py --root . --dry-run
    python reorganize_shared.py --root . --force
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# (source path relative to --root, destination path relative to --root)
FILE_MOVES: list[tuple[str, str]] = [
    ("src/shared/audit.py", "src/shared/audit/audit.py"),
    ("src/shared/audit_context.py", "src/shared/audit/audit_context.py"),
    ("src/shared/audit_types.py", "src/shared/audit/audit_types.py"),
    ("src/shared/cache.py", "src/shared/cache/cache.py"),
    ("src/shared/constants.py", "src/shared/constants/constants.py"),
    ("src/shared/email.py", "src/shared/email/email.py"),
    ("src/shared/helpers.py", "src/shared/helpers/helpers.py"),
    ("src/shared/logger.py", "src/shared/logging/logger.py"),
    ("src/shared/metrics.py", "src/shared/logging/metrics.py"),
    ("src/shared/monitoring.py", "src/shared/monitoring/monitoring.py"),
    ("src/shared/queue.py", "src/shared/queue/queue.py"),
    ("src/shared/scheduling_types.py", "src/shared/scheduling/scheduling_types.py"),
    ("src/shared/security.py", "src/shared/security/security.py"),
    ("src/shared/tickets.py", "src/shared/tickets/tickets.py"),
    ("src/shared/validators.py", "src/shared/validation/validators.py"),

    # Email templates, regrouped by owning domain.
    ("src/shared/templates/base.html", "src/shared/email/templates/base/base.html"),
    ("src/shared/templates/otp.html", "src/shared/email/templates/auth/otp.html"),
    ("src/shared/templates/password_reset.html", "src/shared/email/templates/auth/password_reset.html"),
    ("src/shared/templates/resume_registration.html", "src/shared/email/templates/auth/resume_registration.html"),
    ("src/shared/templates/verification_success.html", "src/shared/email/templates/auth/verification_success.html"),
    ("src/shared/templates/verification_failed.html", "src/shared/email/templates/auth/verification_failed.html"),
    ("src/shared/templates/welcome_business.html", "src/shared/email/templates/business/welcome_business.html"),
    ("src/shared/templates/welcome_supplier.html", "src/shared/email/templates/supplier/welcome_supplier.html"),
    ("src/shared/templates/supplier_invitation.html", "src/shared/email/templates/supplier/supplier_invitation.html"),
    ("src/shared/templates/order_received.html", "src/shared/email/templates/supplier/order_received.html"),
    ("src/shared/templates/order_shipped.html", "src/shared/email/templates/supplier/order_shipped.html"),
    ("src/shared/templates/order_delivered.html", "src/shared/email/templates/supplier/order_delivered.html"),
]

# Every new subpackage needs an __init__.py to be importable.
NEW_PACKAGE_INITS: list[str] = [
    "src/shared/audit/__init__.py",
    "src/shared/audit/event_types/__init__.py",
    "src/shared/cache/__init__.py",
    "src/shared/constants/__init__.py",
    "src/shared/email/__init__.py",
    "src/shared/helpers/__init__.py",
    "src/shared/logging/__init__.py",
    "src/shared/monitoring/__init__.py",
    "src/shared/queue/__init__.py",
    "src/shared/scheduling/__init__.py",
    "src/shared/security/__init__.py",
    "src/shared/tickets/__init__.py",
    "src/shared/validation/__init__.py",
]

# Placeholder files reserving future per-domain audit event splits.
# Comment-only, per your instruction -- no actual enum content moved here.
EVENT_TYPE_PLACEHOLDERS: list[str] = [
    "src/shared/audit/event_types/auth.py",
    "src/shared/audit/event_types/supplier.py",
    "src/shared/audit/event_types/business.py",
    "src/shared/audit/event_types/marketplace.py",
    "src/shared/audit/event_types/verification.py",
    "src/shared/audit/event_types/trust.py",
    "src/shared/audit/event_types/security.py",
    "src/shared/audit/event_types/platform.py",
    "src/shared/audit/event_types/admin.py",
]

EVENT_TYPE_PLACEHOLDER_CONTENT = (
    "# Reserved for future {domain}-specific audit event types.\n"
    "# Not yet in use -- the full AuditEventName enum currently lives in\n"
    "# src/shared/audit/audit_types.py. This file is a placeholder for a\n"
    "# future per-domain split, added by the shared/ reorganization.\n"
)

# Future template categories: no templates exist yet, but the folders
# should exist and be tracked by git (which doesn't track empty dirs),
# so each gets a .gitkeep placeholder.
FUTURE_TEMPLATE_DIRS: list[str] = [
    "src/shared/email/templates/security",
    "src/shared/email/templates/platform",
    "src/shared/email/templates/admin",
]


def _domain_from_placeholder_path(path: str) -> str:
    return Path(path).stem


def do_file_moves(root: Path, force: bool, dry_run: bool) -> tuple[list[str], list[str], list[str]]:
    moved, skipped_missing, skipped_conflict = [], [], []

    for src_rel, dst_rel in FILE_MOVES:
        src = root / src_rel
        dst = root / dst_rel

        if not src.exists():
            skipped_missing.append(src_rel)
            continue

        if dst.exists() and not force:
            skipped_conflict.append(dst_rel)
            continue

        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))

        moved.append(f"{src_rel}  ->  {dst_rel}")

    return moved, skipped_missing, skipped_conflict


def do_create_inits(root: Path, force: bool, dry_run: bool) -> tuple[list[str], list[str]]:
    created, skipped = [], []
    for rel in NEW_PACKAGE_INITS:
        target = root / rel
        if target.exists() and not force:
            skipped.append(rel)
            continue
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("", encoding="utf-8")
        created.append(rel)
    return created, skipped


def do_create_event_type_placeholders(root: Path, force: bool, dry_run: bool) -> tuple[list[str], list[str]]:
    created, skipped = [], []
    for rel in EVENT_TYPE_PLACEHOLDERS:
        target = root / rel
        if target.exists() and not force:
            skipped.append(rel)
            continue
        domain = _domain_from_placeholder_path(rel)
        content = EVENT_TYPE_PLACEHOLDER_CONTENT.format(domain=domain)
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        created.append(rel)
    return created, skipped


def do_create_future_template_dirs(root: Path, dry_run: bool) -> list[str]:
    created = []
    for rel in FUTURE_TEMPLATE_DIRS:
        gitkeep = root / rel / ".gitkeep"
        if gitkeep.exists():
            continue
        if not dry_run:
            gitkeep.parent.mkdir(parents=True, exist_ok=True)
            gitkeep.write_text("", encoding="utf-8")
        created.append(f"{rel}/.gitkeep")
    return created


def cleanup_empty_dirs(root: Path, dry_run: bool) -> list[str]:
    """
    After moving every file out of the old flat src/shared/templates/,
    that directory (and possibly others) is left empty. Remove empty
    directories left behind by the moves above -- but ONLY directories
    this script's own moves could plausibly have emptied, never a blanket
    sweep of the repo.
    """
    candidates = [root / "src/shared/templates"]
    removed = []
    for d in candidates:
        if d.exists() and d.is_dir() and not any(d.iterdir()):
            if not dry_run:
                d.rmdir()
            removed.append(str(d.relative_to(root)))
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", required=True, help="Path to your backend repo root")
    parser.add_argument("--force", action="store_true", help="Overwrite existing destination files")
    parser.add_argument("--dry-run", action="store_true", help="Preview without touching the filesystem")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        print(f"Root path does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    verb = "Would move" if args.dry_run else "Moved"
    moved, skipped_missing, skipped_conflict = do_file_moves(root, args.force, args.dry_run)
    print(f"\n{verb} {len(moved)} file(s):")
    for m in moved:
        print(f"  * {m}")

    if skipped_missing:
        print(f"\nSkipped {len(skipped_missing)} file(s) not found (already moved, or never existed):")
        for s in skipped_missing:
            print(f"  - {s}")

    if skipped_conflict:
        print(f"\nSkipped {len(skipped_conflict)} file(s) — destination already exists (use --force to overwrite):")
        for s in skipped_conflict:
            print(f"  ! {s}")

    verb2 = "Would create" if args.dry_run else "Created"
    inits_created, inits_skipped = do_create_inits(root, args.force, args.dry_run)
    print(f"\n{verb2} {len(inits_created)} __init__.py file(s) for new subpackages.")
    if inits_skipped:
        print(f"Skipped {len(inits_skipped)} __init__.py file(s) that already exist.")

    placeholders_created, placeholders_skipped = do_create_event_type_placeholders(root, args.force, args.dry_run)
    print(f"{verb2} {len(placeholders_created)} event_types/ placeholder file(s) (comment-only, no enum content).")
    if placeholders_skipped:
        print(f"Skipped {len(placeholders_skipped)} event_types/ placeholder file(s) that already exist.")

    template_dirs_created = do_create_future_template_dirs(root, args.dry_run)
    print(f"{verb2} {len(template_dirs_created)} future template folder(s) (security/platform/admin, empty).")

    removed = cleanup_empty_dirs(root, args.dry_run)
    if removed:
        verb3 = "Would remove" if args.dry_run else "Removed"
        print(f"\n{verb3} {len(removed)} now-empty directory(ies):")
        for r in removed:
            print(f"  x {r}")

    print(
        "\nNOTE: src/shared/audit.py.bak was left untouched at its original "
        "location, as agreed.\n"
        "NOTE: import statements inside moved files are now broken and "
        "need a separate fix pass (e.g. audit.py's imports of "
        "audit_context/audit_types) -- this script only relocates files, "
        "it never edits their contents."
    )


if __name__ == "__main__":
    main()