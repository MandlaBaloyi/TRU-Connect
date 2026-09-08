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
    # SEPARATE FROM created_rows, because "we updated 2,800 of your
    # existing lines" and "we added 2,800 new ones" are wildly different
    # outcomes and a supplier must never have to guess which happened.
    # A weekly price file should be almost entirely updates; a first
    # import almost entirely creations. The two numbers side by side are
    # what makes a wrong SKU column visible immediately.
    updated_rows = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    images_total = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    images_matched = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))

    failure_reason = db.Column(db.String(500), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)


class ImportRowOutcome(str, enum.Enum):
    """What happened to one spreadsheet row.

    Name == value, the convention every enum in this codebase follows
    since SQLAlchemy persists a member's NAME rather than its .value.
    """

    CREATED = "CREATED"
    UPDATED = "UPDATED"
    FAILED = "FAILED"


class ImportRow(BaseModel):
    """One row of the supplier's file, and what became of it.

    WHY THIS EXISTS. Before it, an import could say "2,847 rows created"
    and nothing more -- a supplier whose file half-worked had no way to
    find out WHICH lines were affected, and ImportJobError only ever
    recorded failures, never successes. This records every row, so the
    downloadable report can say "COKE-2L updated, BRD-W created" instead
    of a number.

    IT IS ALSO THE SEAM FOR EVERYTHING THAT COMES NEXT. A preview gate
    ("2,847 ready, 112 need review, 41 errors" before anything is
    written) and API ingestion from a supplier's own system both land in
    this table; the preview reads it before commit, the API writes into
    it directly and skips the file stages entirely. Neither exists yet
    and neither needs a second staging concept when it does.

    WRITTEN AFTER THE FACT, NOT BEFORE, in this first version. The flow
    is still upload-then-process with no preview gate, because the
    mobile app is a shipped client and changing the flow would break it.
    That is a UI change, and this table is what makes it possible later
    without another migration.
    """

    __tablename__ = "import_rows"
    __table_args__ = (
        db.Index("ix_import_rows_import_job_id", "import_job_id"),
        {"schema": "supplier"},
    )

    import_job_id = db.Column(UUID(as_uuid=True), db.ForeignKey("supplier.import_jobs.id"), nullable=False)

    #: 1-based, matching what the supplier sees in their spreadsheet --
    #: "row 412" has to mean row 412 to them, not to us.
    row_number = db.Column(db.Integer, nullable=False)

    #: The SKU as the FILE gave it, which is not necessarily the offer's
    #: SKU: a row with the column left blank gets a generated one. Kept
    #: as written so the report can be read against the original file.
    supplier_sku = db.Column(db.String(50), nullable=True)

    outcome = db.Column(
        db.Enum(ImportRowOutcome, name="import_row_outcome", schema="supplier"), nullable=False
    )

    #: NULLABLE, and null for a FAILED row -- there is no offer to point
    #: at. No cascade: an offer being deleted later must not erase the
    #: history of how it got there.
    supplier_offer_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("supplier.supplier_offers.id", ondelete="SET NULL"),
        nullable=True,
    )

    #: Why it failed. Null on success.
    message = db.Column(db.String(500), nullable=True)


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
