"""
A business reporting a concern about a supplier. See SupplierReport's
own model docstring on why this is a real, permanent record today even
though no admin panel exists yet to review it, and why the
notification email is a courtesy on top of that record, never a
replacement for it.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.domains.network.connections.models.supplier_report import SupplierReportReason
from src.domains.network.connections.repositories.supplier_report_repository import SupplierReportRepository
from src.domains.network.connections.services.errors import SupplierNotFoundError
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)


def report_supplier(
    business_id: str | UUID,
    supplier_profile_id: str | UUID,
    reason: str,
    details: Optional[str],
    product_id: Optional[str | UUID] = None,
) -> dict:
    """Deliberately does NOT require an active (or even any) connection
    -- a genuine scam concern should be reportable regardless of
    connection status, unlike ordering or seeing contact details, which
    both genuinely do require one.

    product_id IS OPTIONAL -- set when reported from a specific
    product's own 3-dot menu ("Report this product"), omitted when
    reported from the catalogue's own menu ("Report" the supplier
    generally). When provided, it's verified to genuinely belong to
    THIS supplier first -- same IDOR-safety discipline as every other
    ownership check in this domain; a mismatched product_id is
    silently dropped rather than trusted.

    reason arrives as the schema-validated uppercase string
    (ReportSupplierSchema's own validate.OneOf) -- [] member-name
    lookup, not () value lookup, same as end_connection.
    """
    from flask import current_app

    from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
    from src.shared.email.email import EmailService

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    verified_product_id = None
    product_name = None
    if product_id is not None:
        product = SupplierOfferRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
        if product:
            verified_product_id = product.id
            product_name = product.name

    report = SupplierReportRepository.create(
        business_id, supplier_profile_id, SupplierReportReason[reason], details, product_id=verified_product_id
    )

    reports_email = current_app.config.get("SUPPLIER_REPORTS_EMAIL")
    if reports_email:
        EmailService.send_template(
            to=reports_email,
            template_name="network/supplier_reported.html",
            subject=f"Supplier report: {supplier.business_name}",
            context={
                "supplier_business_name": supplier.business_name,
                "supplier_profile_id": str(supplier_profile_id),
                "product_name": product_name,
                "reason": report.reason.value.replace("_", " ").title(),
                "details": details or "(no additional details provided)",
                "report_id": str(report.id),
            },
        )

    return {"status": "SUBMITTED"}
