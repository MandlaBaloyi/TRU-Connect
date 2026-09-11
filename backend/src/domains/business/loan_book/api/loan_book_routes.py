"""
Loan Book HTTP routes.

AUTH: @fully_authenticated + @role_required("business") on every
route. The first is database-fresh (verified and active NOW, not when
the token was minted); the second is the one that used to be missing
-- these routes pinned no role at all, back when "authenticated" and
"is a business" were the same sentence because only two roles existed.

NOT participants_only, which is the weaker gate used on the genuinely
shared routes (notifications, geocoding, connections). The Loan Book
is not shared: it records which of a shop's CUSTOMERS owe it money. A
supplier has no such book, and neither does a staff account.

business_id is taken from get_jwt_identity() -- the authenticated
caller's own user id -- NEVER from anything in the request body or URL.
This is not a style preference: it's the actual mechanism the whole
ownership model (see services/loan_book_service.py, and
tests/domains/business/loan_book/test_ownership.py) depends on. A route
that read business_id from a request parameter instead would make every
ownership check downstream pointless, since an attacker could simply
claim to be whichever business they wanted.
"""
from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated, role_required
from src.domains.business.loan_book.schemas.loan_book_schemas import (
    CreateCustomerSchema,
    CreateLoanEntrySchema,
    DeleteReasonSchema,
    RecordPaymentSchema,
)
from src.domains.business.loan_book.services.errors import LoanBookNotFoundError, LoanBookValidationError
from src.domains.business.loan_book.services.loan_book_service import LoanBookService
from src.shared.finance import Money, format_for_json

loan_book_bp = Blueprint("loan_book", __name__)


def _business_id() -> uuid.UUID:
    return uuid.UUID(get_jwt_identity())


def _entry_view_to_dict(view) -> dict:
    return {
        "id": str(view.entry.id),
        "customerId": str(view.entry.customer_id),
        "description": view.entry.description,
        "saleDate": view.entry.sale_date.isoformat(),
        "isSettled": view.entry.is_settled,
        "settledAt": view.entry.settled_at.isoformat() if view.entry.settled_at else None,
        "originalAmount": format_for_json(Money(view.entry.original_amount_cents)),
        "amountPaid": format_for_json(view.amount_paid),
        "outstandingAmount": format_for_json(view.outstanding),
        "payments": [_payment_to_dict(p) for p in view.payments],
    }


def _payment_to_dict(payment) -> dict:
    return {
        "id": str(payment.id),
        "amount": format_for_json(Money(payment.amount_cents)),
        "paidAt": payment.paid_at.isoformat(),
        "note": payment.note,
    }


def _customer_to_dict(customer) -> dict:
    return {
        "id": str(customer.id),
        "name": customer.name,
        "phone": customer.phone,
        "firstRecordedAt": customer.first_recorded_at.isoformat(),
        "lastTransactionAt": customer.last_transaction_at.isoformat() if customer.last_transaction_at else None,
        "deletedAt": customer.deleted_at.isoformat() if customer.deleted_at else None,
    }


def _customer_view_to_dict(view: dict) -> dict:
    return {
        "customer": _customer_to_dict(view["customer"]),
        "entries": [_entry_view_to_dict(v) for v in view["entries"]],
        "totalOutstanding": format_for_json(view["total_outstanding"]),
        "openEntryCount": view["open_entry_count"],
    }


# --- Customers ----------------------------------------------------------

@loan_book_bp.route("/api/v1/loan-book/customers", methods=["POST"])
@fully_authenticated
@role_required("business")
def create_customer():
    try:
        data = CreateCustomerSchema().load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as exc:
        return jsonify(success=False, errors=exc.messages), 422

    customer = LoanBookService.create_customer(
        _business_id(), data["name"], data.get("phone"), customer_id=data.get("id")
    )
    return jsonify(success=True, data=_customer_to_dict(customer)), 201


@loan_book_bp.route("/api/v1/loan-book/customers", methods=["GET"])
@fully_authenticated
@role_required("business")
def list_customers():
    views = LoanBookService.list_customer_views(_business_id())
    return jsonify(success=True, data=[_customer_view_to_dict(v) for v in views])


@loan_book_bp.route("/api/v1/loan-book/customers/<uuid:customer_id>", methods=["GET"])
@fully_authenticated
@role_required("business")
def get_customer(customer_id: uuid.UUID):
    try:
        view = LoanBookService.get_customer_view(_business_id(), customer_id)
    except LoanBookNotFoundError:
        return jsonify(success=False, message="Customer not found."), 404
    return jsonify(success=True, data=_customer_view_to_dict(view))


@loan_book_bp.route("/api/v1/loan-book/customers/<uuid:customer_id>", methods=["DELETE"])
@fully_authenticated
@role_required("business")
def delete_customer(customer_id: uuid.UUID):
    data = DeleteReasonSchema().load(request.get_json(silent=True) or {})
    try:
        LoanBookService.delete_customer(_business_id(), customer_id, reason=data.get("reason"))
    except LoanBookNotFoundError:
        return jsonify(success=False, message="Customer not found."), 404
    return jsonify(success=True), 200


@loan_book_bp.route("/api/v1/loan-book/customers/<uuid:customer_id>/restore", methods=["POST"])
@fully_authenticated
@role_required("business")
def restore_customer(customer_id: uuid.UUID):
    try:
        customer = LoanBookService.restore_customer(_business_id(), customer_id)
    except LoanBookNotFoundError:
        return jsonify(success=False, message="Customer not found in trash."), 404
    return jsonify(success=True, data=_customer_to_dict(customer))


# --- Loan entries ---------------------------------------------------------

@loan_book_bp.route("/api/v1/loan-book/entries", methods=["POST"])
@fully_authenticated
@role_required("business")
def create_entry():
    try:
        data = CreateLoanEntrySchema().load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as exc:
        return jsonify(success=False, errors=exc.messages), 422

    try:
        entry = LoanBookService.create_entry(
            _business_id(),
            data["customer_id"],
            Money(data["amount_cents"]),
            description=data.get("description"),
            entry_id=data.get("id"),
        )
    except LoanBookNotFoundError:
        # Same response as "customer doesn't exist" -- see
        # LoanBookNotFoundError's docstring for why this ambiguity is
        # deliberate, not an oversight.
        return jsonify(success=False, message="Customer not found."), 404
    except LoanBookValidationError as exc:
        return jsonify(success=False, message=exc.message, field=exc.field), 422

    view = LoanBookService.get_entry(_business_id(), entry.id)
    return jsonify(success=True, data=_entry_view_to_dict(view)), 201


@loan_book_bp.route("/api/v1/loan-book/entries", methods=["GET"])
@fully_authenticated
@role_required("business")
def list_entries():
    views = LoanBookService.list_entries(_business_id())
    return jsonify(success=True, data=[_entry_view_to_dict(v) for v in views])


@loan_book_bp.route("/api/v1/loan-book/entries/<uuid:entry_id>", methods=["GET"])
@fully_authenticated
@role_required("business")
def get_entry(entry_id: uuid.UUID):
    try:
        view = LoanBookService.get_entry(_business_id(), entry_id)
    except LoanBookNotFoundError:
        return jsonify(success=False, message="Entry not found."), 404
    return jsonify(success=True, data=_entry_view_to_dict(view))


@loan_book_bp.route("/api/v1/loan-book/entries/<uuid:entry_id>", methods=["DELETE"])
@fully_authenticated
@role_required("business")
def delete_entry(entry_id: uuid.UUID):
    data = DeleteReasonSchema().load(request.get_json(silent=True) or {})
    try:
        LoanBookService.delete_entry(_business_id(), entry_id, reason=data.get("reason"))
    except LoanBookNotFoundError:
        return jsonify(success=False, message="Entry not found."), 404
    return jsonify(success=True), 200


@loan_book_bp.route("/api/v1/loan-book/entries/<uuid:entry_id>/restore", methods=["POST"])
@fully_authenticated
@role_required("business")
def restore_entry(entry_id: uuid.UUID):
    try:
        entry = LoanBookService.restore_entry(_business_id(), entry_id)
    except LoanBookNotFoundError:
        return jsonify(success=False, message="Entry not found in trash."), 404
    view = LoanBookService.get_entry(_business_id(), entry.id)
    return jsonify(success=True, data=_entry_view_to_dict(view))


# --- Payments -------------------------------------------------------------

@loan_book_bp.route("/api/v1/loan-book/entries/<uuid:entry_id>/payments", methods=["POST"])
@fully_authenticated
@role_required("business")
def record_payment(entry_id: uuid.UUID):
    try:
        data = RecordPaymentSchema().load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as exc:
        return jsonify(success=False, errors=exc.messages), 422

    try:
        view = LoanBookService.record_payment(
            _business_id(),
            entry_id,
            Money(data["amount_cents"]),
            note=data.get("note"),
            payment_id=data.get("id"),
        )
    except LoanBookNotFoundError:
        return jsonify(success=False, message="Entry not found."), 404
    except LoanBookValidationError as exc:
        return jsonify(success=False, message=exc.message, field=exc.field), 422

    return jsonify(success=True, data=_entry_view_to_dict(view)), 201


@loan_book_bp.route(
    "/api/v1/loan-book/entries/<uuid:entry_id>/payments/<uuid:payment_id>", methods=["DELETE"]
)
@fully_authenticated
@role_required("business")
def delete_payment(entry_id: uuid.UUID, payment_id: uuid.UUID):
    try:
        view = LoanBookService.delete_payment(_business_id(), entry_id, payment_id)
    except LoanBookNotFoundError:
        return jsonify(success=False, message="Entry or payment not found."), 404
    return jsonify(success=True, data=_entry_view_to_dict(view))


# --- Transaction history ---------------------------------------------

def _history_event_to_dict(event) -> dict:
    return {
        "id": str(event.id),
        "customerId": str(event.customer_id),
        "loanEntryId": str(event.loan_entry_id) if event.loan_entry_id else None,
        "eventType": event.event_type.value,
        "amount": format_for_json(Money(event.amount_cents)) if event.amount_cents is not None else None,
        "description": event.description,
        "reason": event.reason,
        "occurredAt": event.occurred_at.isoformat(),
    }


@loan_book_bp.route("/api/v1/loan-book/history", methods=["GET"])
@fully_authenticated
@role_required("business")
def get_transaction_history():
    events = LoanBookService.get_transaction_history(_business_id())
    return jsonify(success=True, data=[_history_event_to_dict(e) for e in events])


# --- Receipt ------------------------------------------------------------

@loan_book_bp.route("/api/v1/loan-book/entries/<uuid:entry_id>/receipt", methods=["GET"])
@fully_authenticated
@role_required("business")
def get_receipt(entry_id: uuid.UUID):
    from src.domains.business.loan_book.utils.receipt_builder import build_receipt_data

    try:
        view = LoanBookService.get_entry(_business_id(), entry_id)
        customer = LoanBookService.get_customer(_business_id(), view.entry.customer_id)
    except LoanBookNotFoundError:
        return jsonify(success=False, message="Entry not found."), 404

    receipt = build_receipt_data(view, customer.name)
    return jsonify(
        success=True,
        data={
            "referenceCode": receipt.reference_code,
            "customerName": receipt.customer_name,
            "fromLabel": receipt.from_label,
            "saleDateLabel": receipt.sale_date_label,
            "description": receipt.description,
            "originalAmountLabel": receipt.original_amount_label,
            "amountPaidLabel": receipt.amount_paid_label,
            "outstandingAmountLabel": receipt.outstanding_amount_label,
            "isSettled": receipt.is_settled,
            "isPartlyPaid": receipt.is_partly_paid,
        },
    )


# --- Trash ------------------------------------------------------------

@loan_book_bp.route("/api/v1/loan-book/trash", methods=["GET"])
@fully_authenticated
@role_required("business")
def get_trash():
    trash = LoanBookService.get_trash(_business_id())
    return jsonify(
        success=True,
        data={
            "customers": [
                {
                    **_customer_to_dict(c["customer"]),
                    "openEntryCount": c["open_entry_count"],
                    "totalEntryCount": c["total_entry_count"],
                    "totalOutstanding": format_for_json(c["total_outstanding"]),
                }
                for c in trash["customers"]
            ],
            "entries": [
                {
                    "id": str(e.id),
                    "customerId": str(e.customer_id),
                    "description": e.description,
                    "originalAmount": format_for_json(Money(e.original_amount_cents)),
                    "deletionReason": e.deletion_reason,
                    "deletedAt": e.deleted_at.isoformat() if e.deleted_at else None,
                }
                for e in trash["entries"]
            ],
        },
    )
