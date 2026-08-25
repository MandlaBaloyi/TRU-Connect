"""
The Bulk Import worker -- runs on the shared background queue
(src/shared/queue), wrapped in app.app_context() the same way
audit_service._write_async already establishes as this codebase's own
pattern for exactly this problem (a bare worker thread has no Flask
context of its own).

PER ROW, THIS CALLS THE EXACT SAME FUNCTIONS Add Product'S OWN SCREEN
CALLS -- product_service.create_product, then inventory_service.
adjust_stock if a quantity was given. Per direct review: "don't have
single-product validation != bulk-product validation... one Product
Service, same validation rules." This file contains NO product-
creation logic of its own; it's an orchestrator, not a second
implementation.

TWO TIER-GATED CHECKS LIVE HERE, NOT IN THE PARSERS -- bulk_max_rows_
per_job and bulk_max_images_per_job (products/tiers/*.py). The parsers
(spreadsheet_parser.MAX_ROWS, zip_parser.MAX_ENTRY_COUNT) enforce hard,
tier-agnostic TECHNICAL safety ceilings; these two are the actual
BUSINESS limits for the account's plan, checked here because this is
where the account's tier is known. Per-image SIZE is enforced one
layer down, inside product_media_service.upload_and_register_from_bytes
(shared with the single-product upload path) -- this file doesn't
duplicate that check, it just handles what that function raises.

PROGRESS IS WRITTEN TO THE DATABASE AS THE WORKER GOES, not only at
the end -- the whole reason ImportJob is a real table and not an
in-memory counter (see that model's own docstring on why: the queue
itself doesn't survive a process restart, but the DB row does).
"""
from __future__ import annotations

import difflib
import logging
import os
import tempfile
from typing import Dict, Optional
from uuid import UUID

from src.domains.supplier.bulk_import.models.import_job import ImportJobStatus
from src.domains.supplier.bulk_import.parsers.spreadsheet_parser import UnsafeSpreadsheetError, parse_spreadsheet
from src.domains.supplier.bulk_import.parsers.zip_parser import UnsafeZipError, extract_image_bytes, inspect_zip
from src.domains.supplier.bulk_import.repositories.import_job_repository import ImportJobRepository
from src.domains.supplier.bulk_import.services import abuse_tracking
from src.domains.supplier.bulk_import.validators.row_validator import RowError
from src.domains.supplier.inventory.services import inventory_service
from src.domains.supplier.products.services import product_media_service, product_service
from src.domains.supplier.products.services.errors import ProductValidationError
from src.domains.supplier.products.tiers import get_products_limits
from src.domains.supplier.tiers.resolver import get_current_tier
from src.shared.media.errors import MediaUploadQuotaExceededError, PhotoLimitExceededError

logger = logging.getLogger(__name__)


def run_import(
    job_id: str | UUID,
    supplier_profile_id: str | UUID,
    spreadsheet_filename: str,
    spreadsheet_bytes: bytes,
    zip_filename: Optional[str],
    zip_bytes: Optional[bytes],
) -> None:
    job = ImportJobRepository.get_by_id_and_supplier(job_id, supplier_profile_id)
    if job is None:
        logger.error("import worker: job %s not found, aborting", job_id)
        return

    try:
        _run(job, supplier_profile_id, spreadsheet_filename, spreadsheet_bytes, zip_filename, zip_bytes)
    except Exception as exc:  # noqa: BLE001 - a failing job must land in FAILED, never crash the worker thread
        logger.exception("import worker: job %s failed unexpectedly", job_id)
        ImportJobRepository.set_status(job, ImportJobStatus.FAILED, failure_reason=str(exc)[:500])


def _run(
    job,
    supplier_profile_id: str | UUID,
    spreadsheet_filename: str,
    spreadsheet_bytes: bytes,
    zip_filename: Optional[str],
    zip_bytes: Optional[bytes],
) -> None:
    limits = get_products_limits(get_current_tier(supplier_profile_id))

    ImportJobRepository.set_status(job, ImportJobStatus.VALIDATING)

    try:
        parsed = parse_spreadsheet(spreadsheet_filename, spreadsheet_bytes)
    except UnsafeSpreadsheetError as exc:
        ImportJobRepository.add_error(job.id, row_number=0, field="_file", message=str(exc))
        ImportJobRepository.commit()
        ImportJobRepository.set_status(job, ImportJobStatus.FAILED, failure_reason=str(exc))
        return

    # Tier's own row-count ceiling -- distinct from, and always <=,
    # spreadsheet_parser.MAX_ROWS's own hard technical ceiling (see
    # that file's own docstring). Fails the whole job with a clear
    # message rather than silently truncating to the first N rows,
    # which would process an incomplete file without the supplier
    # necessarily realising it.
    if len(parsed.rows) > limits.bulk_max_rows_per_job:
        message = (
            f"This file has {len(parsed.rows)} rows -- your plan allows up to "
            f"{limits.bulk_max_rows_per_job} rows per import."
        )
        ImportJobRepository.add_error(job.id, row_number=0, field="_file", message=message)
        ImportJobRepository.commit()
        ImportJobRepository.set_status(job, ImportJobStatus.FAILED, failure_reason=message)
        return

    for column in parsed.missing_required_columns:
        ImportJobRepository.add_error(
            job.id, row_number=0, field=column, message=f"Missing required column: {column}"
        )

    image_bytes_by_filename: Dict[str, bytes] = {}
    if zip_bytes is not None:
        # ONE temp file, reused for both the inspect pass and the
        # extract pass -- inspect_zip/extract_image_bytes both work
        # from a real file path (not in-memory bytes) so the same
        # streaming/lazy-read behaviour they were built and tested
        # against applies here too, not a separate in-memory code path.
        #
        # REAL BUG FOUND DURING WINDOWS DEVICE TESTING -- delete=False
        # HERE ON PURPOSE, file explicitly closed before being reopened
        # by path. On POSIX, a file can be opened by a second handle
        # while the first is still held open in the same process; on
        # Windows, NamedTemporaryFile's default sharing mode does NOT
        # allow this and raises a real PermissionError the instant
        # inspect_zip/extract_image_bytes try to reopen tmp.name while
        # the original `with` block still held it -- confirmed directly
        # from a real Windows traceback, not assumed. Every test this
        # whole build ran before real device testing ran on Linux,
        # which never surfaces this class of bug at all -- this is now
        # written to be correct on both platforms, not just "happened
        # to work in one sandbox." Cleanup is explicit (finally), since
        # delete=False means nothing removes this file automatically.
        tmp_path: Optional[str] = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp_path = tmp.name
                tmp.write(zip_bytes)
            # tmp is now CLOSED -- safe to reopen by path on every
            # platform, including Windows.

            try:
                zip_entries = inspect_zip(tmp_path)
            except UnsafeZipError as exc:
                if exc.is_malicious:
                    abuse_tracking.record_violation(supplier_profile_id)
                ImportJobRepository.add_error(job.id, row_number=0, field="_zip", message=str(exc))
                ImportJobRepository.commit()
                ImportJobRepository.set_status(job, ImportJobStatus.FAILED, failure_reason=str(exc))
                return

            known_filenames = {e.filename for e in zip_entries}
            known_filenames_lower = {name.lower(): name for name in known_filenames}

            # Cross-reference: a row referencing an image filename NOT
            # in the zip is a hard row error -- matches the frontend's
            # own applyImageManifest exactly (see that file's own
            # docstring for why this is a hard error, not a warning).
            #
            # CASE DIFFERENCES ARE RESOLVED AUTOMATICALLY -- "Coke500.jpg"
            # in the spreadsheet against "coke500.jpg" in the ZIP can
            # only ever mean the same file; case is never genuinely
            # ambiguous, unlike a real typo. When a case-insensitive
            # match is found, ref.filename is REWRITTEN to the real ZIP
            # filename so every downstream use (extraction below, the
            # image_bytes_by_filename dict) works off one single,
            # correctly-cased value from here on.
            #
            # A GENUINE MISS GETS A "DID YOU MEAN?" SUGGESTION, NEVER AN
            # AUTO-CORRECTION -- a real typo ("coke50.jpg" vs
            # "coke500.jpg") IS ambiguous; silently guessing could
            # attach the wrong photo to the wrong product, which is
            # worse than an honest error a human confirms.
            for row in parsed.rows:
                for ref in row.image_references:
                    if ref.filename in known_filenames:
                        continue
                    real_name = known_filenames_lower.get(ref.filename.lower())
                    if real_name is not None:
                        ref.filename = real_name
                        continue
                    message = f'Image not found in ZIP: "{ref.filename}".'
                    suggestion = difflib.get_close_matches(ref.filename, known_filenames, n=1, cutoff=0.6)
                    if suggestion:
                        message += f' Did you mean "{suggestion[0]}"?'
                    row.errors.append(RowError(ref.column, message))

            target_filenames = {ref.filename for row in parsed.rows for ref in row.image_references}
            if target_filenames:
                image_bytes_by_filename = extract_image_bytes(tmp_path, target_filenames)
        finally:
            if tmp_path is not None and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    else:
        # No zip uploaded, but rows reference images -- every such
        # reference is unsatisfiable, same as the frontend's own
        # "image referenced but no ZIP was uploaded" case.
        for row in parsed.rows:
            for ref in row.image_references:
                row.errors.append(
                    RowError(ref.column, f'Image referenced ("{ref.filename}") but no ZIP was uploaded.')
                )

    total_rows = len(parsed.rows)
    valid_rows = [r for r in parsed.rows if r.is_valid]
    error_rows = [r for r in parsed.rows if not r.is_valid]

    for row in error_rows:
        for err in row.errors:
            ImportJobRepository.add_error(job.id, row_number=row.row_number, field=err.field, message=err.message)
    ImportJobRepository.commit()

    total_image_refs = sum(len(r.image_references) for r in parsed.rows)
    ImportJobRepository.update_counts(
        job,
        total_rows=total_rows,
        valid_rows=len(valid_rows),
        error_rows=len(error_rows),
        images_total=total_image_refs,
    )

    ImportJobRepository.set_status(job, ImportJobStatus.PROCESSING)

    created_count = 0
    images_matched_count = 0
    # Tier's own JOB-WIDE image ceiling -- distinct from
    # photos_per_product (enforced per-product, one layer down, inside
    # product_media_service). This one caps the TOTAL images uploaded
    # across the whole job, protecting against "1,000 rows x 5 images
    # each" even when every individual product would stay under its
    # own per-product limit. Once hit, remaining rows still create
    # products (and still seed inventory) -- only image upload stops,
    # with ONE clear job-level error rather than one per skipped image.
    bulk_image_cap_hit = False

    for row in valid_rows:
        try:
            product = product_service.create_product(
                supplier_profile_id=supplier_profile_id,
                name=row.name,
                category=row.category,
                price_cents=row.price_cents,
                selling_unit=row.selling_unit,
                sku=row.sku,
                description=row.description,
                compare_at_price_cents=row.compare_at_price_cents,
            )
        except ProductValidationError as exc:
            # The row passed THIS file's own validation but the shared
            # Product Service found something else wrong (e.g. a
            # length cap) -- recorded as a real error; the row simply
            # doesn't create a product. Never crashes the whole job.
            ImportJobRepository.add_error(job.id, row.row_number, "_product", "; ".join(exc.errors))
            ImportJobRepository.commit()
            continue

        created_count += 1

        if row.quantity and row.quantity > 0:
            inventory_service.adjust_stock(
                product_id=product.id,
                supplier_profile_id=supplier_profile_id,
                quantity_delta=row.quantity,
                reason="STOCK_RECEIVED",
            )

        for ref in row.image_references:
            file_bytes = image_bytes_by_filename.get(ref.filename)
            if file_bytes is None:
                continue

            if images_matched_count >= limits.bulk_max_images_per_job:
                if not bulk_image_cap_hit:
                    bulk_image_cap_hit = True
                    ImportJobRepository.add_error(
                        job.id,
                        0,
                        "_file",
                        f"Your plan allows up to {limits.bulk_max_images_per_job} images per import -- "
                        "remaining images in this file weren't uploaded.",
                    )
                    ImportJobRepository.commit()
                continue

            try:
                product_media_service.upload_and_register_from_bytes(product.id, supplier_profile_id, file_bytes)
                images_matched_count += 1
            except (PhotoLimitExceededError, MediaUploadQuotaExceededError) as exc:
                # The product itself already exists -- a per-product or
                # account-wide media limit only skips THIS image, never
                # rolls back the product that was already successfully
                # created.
                ImportJobRepository.add_error(job.id, row.row_number, ref.column, str(exc))

        ImportJobRepository.commit()

    ImportJobRepository.update_counts(job, created_rows=created_count, images_matched=images_matched_count)
    ImportJobRepository.set_status(job, ImportJobStatus.COMPLETED)
