"""
SupplierReport -- a business reporting a concern about a supplier
(counterfeit goods, a suspected scam, and so on), OR about one
specific product from that supplier. Lives in network/connections
alongside ConnectionRequest, not its own domain -- same reasoning as
that model's own docstring on why this domain holds concepts that
belong to the business-supplier relationship itself, not to either
side alone.

REAL TODAY, EVEN THOUGH NO ADMIN PANEL EXISTS YET TO REVIEW THESE --
every report is a genuine, permanent database row the moment it's
submitted, notified out via a real email (see
supplier_reports_service.py) to whoever's watching that inbox until a
proper Control Centre exists to read these directly. `status` is
modelled now, matching this domain's own established "model the future
transition now, extend later rather than re-migrate" precedent
(ConnectionRequestStatus's own docstring) -- nothing currently
transitions a report away from NEW, but the column exists so a future
review flow doesn't need a new migration just to record "someone
looked at this".
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class SupplierReportReason(str, enum.Enum):
    FAKE_PRODUCTS = "fake_products"
    SUSPECTED_SCAM = "suspected_scam"
    ORDER_NOT_RECEIVED = "order_not_received"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    OTHER = "other"


class SupplierReportStatus(str, enum.Enum):
    """No admin panel exists yet to transition these -- every report
    starts, and today stays, NEW. See this module's own docstring on
    why the column exists regardless."""

    NEW = "new"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"


class SupplierReport(BaseModel):
    __tablename__ = "supplier_reports"
    __table_args__ = (
        db.Index("ix_supplier_reports_business_id", "business_id"),
        db.Index("ix_supplier_reports_supplier_profile_id", "supplier_profile_id"),
        db.Index("ix_supplier_reports_product_id", "product_id"),
        {"schema": "network"},
    )

    business_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)
    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
    )
    # Nullable -- the same underlying report mechanism serves two entry
    # points: the Stock Catalogue's own 3-dot menu ("Report" the
    # supplier generally, no product_id) and a specific product's own
    # 3-dot menu ("Report this product", product_id set). One report
    # table, one email template, one review flow either way -- a
    # product-level report is genuinely still a report ABOUT that
    # supplier, just with a real product attached for context.
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey("supplier.supplier_offers.id"), nullable=True)
    reason = db.Column(
        db.Enum(SupplierReportReason, name="supplier_report_reason", schema="network"), nullable=False
    )
    # Optional even when reason isn't OTHER -- a business reporting
    # SUSPECTED_SCAM might reasonably want to add real specifics
    # without that meaning the reason itself was ambiguous.
    details = db.Column(db.String(1000), nullable=True)
    status = db.Column(
        db.Enum(SupplierReportStatus, name="supplier_report_status", schema="network"),
        nullable=False,
        default=SupplierReportStatus.NEW,
    )
