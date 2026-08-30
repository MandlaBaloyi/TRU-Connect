"""
SupplierReport repository -- ONLY talks to SQLAlchemy, no business
rules, same discipline as connection_request_repository.py's own
docstring.
"""
from __future__ import annotations

from uuid import UUID

from src.domains.network.connections.models.supplier_report import SupplierReport, SupplierReportReason
from src.extensions import db


class SupplierReportRepository:
    @staticmethod
    def create(
        business_id: str | UUID,
        supplier_profile_id: str | UUID,
        reason: SupplierReportReason,
        details: str | None,
        product_id: str | UUID | None = None,
    ) -> SupplierReport:
        report = SupplierReport(
            business_id=business_id,
            supplier_profile_id=supplier_profile_id,
            product_id=product_id,
            reason=reason,
            details=details,
        )
        db.session.add(report)
        db.session.commit()
        return report
