"""
Base Model Mixin.
Ref: backend master prompt, "DATABASE" -- UUID primary keys, timezone-
aware timestamps, soft-delete + future audit support on every table.

Every SQLAlchemy model in src/models should inherit from BaseModel rather
than redeclaring id/timestamps/soft-delete columns individually -- this
is what "no duplicated code" means at the schema level. See
docs/04_DATABASE_DESIGN.txt, Section 19 (Relational Design Notes) --
soft-deletes are used in place of hard deletes for Businesses, Suppliers,
Orders, and Verification Records specifically to preserve the Trust
Domain's historical data integrity.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from src.extensions import db


def utcnow() -> datetime:
    """Timezone-aware "now", used as the default/onupdate for every
    timestamp column -- never use naive datetimes in this codebase."""
    return datetime.now(timezone.utc)


class BaseModel(db.Model):
    """Abstract base providing a UUID primary key, timezone-aware
    created_at/updated_at, and soft-delete columns for every TRU Connect
    table. Concrete models set __tablename__ and their own columns."""

    __abstract__ = True

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def soft_delete(self) -> None:
        """Marks this row as deleted without removing it -- callers
        should filter is_deleted=False in repository queries rather than
        relying on the row being physically absent."""
        self.is_deleted = True
        self.deleted_at = utcnow()
