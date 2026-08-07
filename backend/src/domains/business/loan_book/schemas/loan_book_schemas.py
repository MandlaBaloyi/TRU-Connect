"""
Loan Book request/response schemas.

Field names use data_key to match the mobile app's camelCase wire
format (frontend Loan Book's types.ts) exactly -- same convention
already established in auth_schemas.py.

Amount fields use `amount_cents`/`original_amount_cents` naming, never
a bare `amount` -- so nobody reading a request or response has to guess
whether a number means cents or rands. Same reasoning already applied
throughout the Finance Engine's own API surface.

NOTE: outgoing Money values are NOT serialized by a Schema here -- the
route layer calls shared.finance.format_for_json() directly, which
already returns the exact {minor_units, currency, formatted} shape
every response uses. These schemas only validate INCOMING requests.
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate


class CreateCustomerSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    phone = fields.String(required=False, allow_none=True, validate=validate.Length(max=20))
    # Optional client-supplied id -- see LoanBookService.create_customer()
    # docstring for why this matters for offline-first sync.
    id = fields.UUID(required=False, allow_none=True)


class CreateLoanEntrySchema(Schema):
    customer_id = fields.UUID(required=True, data_key="customerId")
    amount_cents = fields.Integer(required=True, data_key="amountCents", validate=validate.Range(min=1))
    description = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))
    id = fields.UUID(required=False, allow_none=True)


class RecordPaymentSchema(Schema):
    amount_cents = fields.Integer(required=True, data_key="amountCents", validate=validate.Range(min=1))
    note = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))
    id = fields.UUID(required=False, allow_none=True)


class DeleteReasonSchema(Schema):
    reason = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))
