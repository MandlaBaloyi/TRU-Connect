"""
ImportJob -- the real, DB-backed progress record behind Bulk Import's
"Uploading... Validating... Processing..." UI. DB-backed deliberately,
not held in memory: the shared background queue (src/shared/queue) is
explicitly an in-process placeholder with nothing persisted -- if the
process restarts mid-import, a supplier needs to see exactly how far
their import got, not have it silently vanish. Writing progress to
this table as the worker goes (not just at the end) is what makes that
true.

ImportJobError -- one row per row-level validation failure, exactly
what the downloadable error report reads from. A separate table, not
a JSON blob on ImportJob, so it can be queried/paginated/downloaded
without ever loading the whole error list into memory at once for a
job with thousands of failed rows.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class ImportJobStatus(str, enum.Enum):
    """Same name==value convention as every other enum in this
    codebase. UPLOADED is the only status the HTTP request itself ever
    sets -- everything after that is the background worker's own
    progression, never set synchronously."""

    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ImportJob(BaseModel):
    __tablename__ = "import_jobs"
    __table_args__ = (
        db.Index("ix_import_jobs_supplier_profile_id", "supplier_profile_id"),
        {"schema": "supplier"},
    )

    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
    )
    status = db.Column(
        db.Enum(ImportJobStatus, name="import_job_status", schema="supplier"),
        nullable=False,
        default=ImportJobStatus.UPLOADED,
    )
    source_filename = db.Column(db.String(255), nullable=False)
    has_images_zip = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())

    total_rows = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    valid_rows = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    error_rows = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    created_rows = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    images_total = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    images_matched = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))

    failure_reason = db.Column(db.String(500), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)


class ImportJobError(BaseModel):
    __tablename__ = "import_job_errors"
    __table_args__ = (
        db.Index("ix_import_job_errors_import_job_id", "import_job_id"),
        {"schema": "supplier"},
    )

    import_job_id = db.Column(UUID(as_uuid=True), db.ForeignKey("supplier.import_jobs.id"), nullable=False)
    row_number = db.Column(db.Integer, nullable=False)
    field = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(500), nullable=False)
