"""
ImportJob/ImportJobError repository -- pure SQL, no business rules,
same rule as every other repository in this codebase.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from src.domains.supplier.bulk_import.models.import_job import (
    ImportJob,
    ImportJobError,
    ImportJobStatus,
    ImportRow,
    ImportRowOutcome,
)
from src.extensions import db


class ImportJobRepository:
    @staticmethod
    def create(supplier_profile_id: str | UUID, source_filename: str, has_images_zip: bool) -> ImportJob:
        job = ImportJob(
            supplier_profile_id=supplier_profile_id,
            status=ImportJobStatus.UPLOADED,
            source_filename=source_filename,
            has_images_zip=has_images_zip,
        )
        db.session.add(job)
        db.session.commit()
        return job

    @staticmethod
    def get_by_id_and_supplier(job_id: str | UUID, supplier_profile_id: str | UUID) -> Optional[ImportJob]:
        return ImportJob.query.filter_by(
            id=job_id, supplier_profile_id=supplier_profile_id, is_deleted=False
        ).first()

    @staticmethod
    def list_for_supplier(supplier_profile_id: str | UUID) -> List[ImportJob]:
        return (
            ImportJob.query.filter_by(supplier_profile_id=supplier_profile_id, is_deleted=False)
            .order_by(ImportJob.created_at.desc())
            .all()
        )

    @staticmethod
    def set_status(job: ImportJob, status: ImportJobStatus, failure_reason: Optional[str] = None) -> ImportJob:
        job.status = status
        if failure_reason is not None:
            job.failure_reason = failure_reason
        if status in (ImportJobStatus.COMPLETED, ImportJobStatus.FAILED):
            job.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        return job

    @staticmethod
    def update_counts(
        job: ImportJob,
        total_rows: Optional[int] = None,
        valid_rows: Optional[int] = None,
        error_rows: Optional[int] = None,
        created_rows: Optional[int] = None,
        updated_rows: Optional[int] = None,
        images_total: Optional[int] = None,
        images_matched: Optional[int] = None,
    ) -> ImportJob:
        if total_rows is not None:
            job.total_rows = total_rows
        if valid_rows is not None:
            job.valid_rows = valid_rows
        if error_rows is not None:
            job.error_rows = error_rows
        if created_rows is not None:
            job.created_rows = created_rows
        if updated_rows is not None:
            job.updated_rows = updated_rows
        if images_total is not None:
            job.images_total = images_total
        if images_matched is not None:
            job.images_matched = images_matched
        db.session.commit()
        return job

    @staticmethod
    def add_error(job_id: str | UUID, row_number: int, field: str, message: str) -> ImportJobError:
        error = ImportJobError(import_job_id=job_id, row_number=row_number, field=field, message=message)
        db.session.add(error)
        return error

    @staticmethod
    def commit() -> None:
        """Lets the worker batch many add_error() calls into one
        commit rather than round-tripping to the database per row --
        matters for a 10,000-row file."""
        db.session.commit()

    @staticmethod
    def list_errors(job_id: str | UUID) -> List[ImportJobError]:
        return (
            ImportJobError.query.filter_by(import_job_id=job_id).order_by(ImportJobError.row_number.asc()).all()
        )

    # ------------------------------------------------------------------
    # Per-row outcomes
    # ------------------------------------------------------------------

    @staticmethod
    def add_row(
        job_id: str | UUID,
        row_number: int,
        outcome: ImportRowOutcome,
        supplier_sku: Optional[str] = None,
        supplier_offer_id: Optional[str | UUID] = None,
        message: Optional[str] = None,
    ) -> ImportRow:
        """One row's fate. NOT committed here -- the worker batches
        these into one commit the same way add_error() is batched, which
        is what keeps a 10,000-row file from doing 10,000 round trips."""
        row = ImportRow(
            import_job_id=job_id,
            row_number=row_number,
            outcome=outcome,
            supplier_sku=supplier_sku,
            supplier_offer_id=supplier_offer_id,
            message=message,
        )
        db.session.add(row)
        return row

    @staticmethod
    def list_rows(job_id: str | UUID) -> List[ImportRow]:
        return ImportRow.query.filter_by(import_job_id=job_id).order_by(ImportRow.row_number.asc()).all()

    @staticmethod
    def count_rows_by_outcome(job_id: str | UUID) -> dict:
        """Counted in SQL rather than by loading every row -- the same
        reason ImportJobError is a table and not a JSON blob."""
        rows = (
            db.session.query(ImportRow.outcome, db.func.count(ImportRow.id))
            .filter(ImportRow.import_job_id == job_id)
            .group_by(ImportRow.outcome)
            .all()
        )
        return {outcome.value: count for outcome, count in rows}
