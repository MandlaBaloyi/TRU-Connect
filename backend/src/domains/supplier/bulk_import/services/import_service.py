"""
ImportService -- the HTTP-facing orchestration layer. Deliberately
thin: create the ImportJob row (fast, synchronous, so the 202 response
can include a real job id), enqueue the worker, return immediately.
ALL actual parsing/validation/row-processing happens in
workers/import_worker.py, on the background queue -- this keeps the
request itself fast regardless of file size, matching "avoid
synchronous... processing in Flask request handlers".

RAW UPLOAD SIZE IS CHECKED HERE, BEFORE ANYTHING ELSE TOUCHES THE
BYTES -- a distinct, earlier gate than spreadsheet_parser.py's own
MAX_FILE_BYTES/zip_parser.py's own uncompressed-size checks (which
only run once the worker gets to them). Rejecting an oversized upload
at the HTTP layer means Flask never has to hold an enormous file in
memory even transiently.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.domains.supplier.bulk_import.models.import_job import ImportJob, ImportJobError
from src.domains.supplier.bulk_import.repositories.import_job_repository import ImportJobRepository
from src.domains.supplier.bulk_import.services.errors import ImportJobNotFoundError, ImportUploadValidationError
from src.domains.supplier.bulk_import.workers.import_worker import run_import

MAX_SPREADSHEET_UPLOAD_BYTES = 20 * 1024 * 1024  # matches spreadsheet_parser.MAX_FILE_BYTES exactly
MAX_ZIP_UPLOAD_BYTES = 220 * 1024 * 1024  # headroom above zip_parser.MAX_TOTAL_UNCOMPRESSED_BYTES


def submit_import(
    supplier_profile_id: str | UUID,
    spreadsheet_filename: str,
    spreadsheet_bytes: bytes,
    zip_filename: Optional[str],
    zip_bytes: Optional[bytes],
) -> ImportJob:
    if len(spreadsheet_bytes) > MAX_SPREADSHEET_UPLOAD_BYTES:
        raise ImportUploadValidationError(
            "Spreadsheet is too large.",
            errors=[f"Spreadsheet must be under {MAX_SPREADSHEET_UPLOAD_BYTES // (1024 * 1024)}MB."],
        )
    if zip_bytes is not None and len(zip_bytes) > MAX_ZIP_UPLOAD_BYTES:
        raise ImportUploadValidationError(
            "Images ZIP is too large.", errors=[f"ZIP must be under {MAX_ZIP_UPLOAD_BYTES // (1024 * 1024)}MB."]
        )

    job = ImportJobRepository.create(
        supplier_profile_id=supplier_profile_id,
        source_filename=spreadsheet_filename,
        has_images_zip=zip_bytes is not None,
    )

    _enqueue_worker(job.id, supplier_profile_id, spreadsheet_filename, spreadsheet_bytes, zip_filename, zip_bytes)
    return job


def _enqueue_worker(
    job_id, supplier_profile_id, spreadsheet_filename, spreadsheet_bytes, zip_filename, zip_bytes
) -> None:
    from flask import current_app

    from src.shared.queue.queue import enqueue

    # Same "capture app via closure, open app_context() inside the
    # deferred callable" pattern as audit_service._write_async -- a
    # bare worker thread has no Flask context of its own, confirmed
    # against this codebase's own prior fix for exactly this class of
    # bug.
    app = current_app._get_current_object()

    def _job() -> None:
        with app.app_context():
            run_import(job_id, supplier_profile_id, spreadsheet_filename, spreadsheet_bytes, zip_filename, zip_bytes)

    enqueue(_job)


def get_import_job(job_id: str | UUID, supplier_profile_id: str | UUID) -> ImportJob:
    job = ImportJobRepository.get_by_id_and_supplier(job_id, supplier_profile_id)
    if not job:
        raise ImportJobNotFoundError("Import job not found.")
    return job


def list_import_jobs(supplier_profile_id: str | UUID) -> List[ImportJob]:
    return ImportJobRepository.list_for_supplier(supplier_profile_id)


def get_import_errors(job_id: str | UUID, supplier_profile_id: str | UUID) -> List[ImportJobError]:
    job = get_import_job(job_id, supplier_profile_id)  # ownership check, same rule as every other domain
    return ImportJobRepository.list_errors(job.id)
