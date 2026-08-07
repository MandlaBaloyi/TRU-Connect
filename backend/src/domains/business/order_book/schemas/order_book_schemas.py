"""
Order Book request/response schemas.

Field names use data_key to match the mobile app's camelCase wire
format (frontend order-book/types.ts) exactly -- same convention as
loan_book_schemas.py.

NOTE: outgoing Money values are NOT serialized by a Schema here -- the
route layer calls shared.finance.format_for_json() directly, same as
Loan Book. These schemas only validate INCOMING requests.
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate


class CreateOrderLineItemSchema(Schema):
    description = fields.String(required=True, validate=validate.Length(min=1, max=300))
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    unit_price_cents = fields.Integer(required=True, data_key="unitPriceCents", validate=validate.Range(min=0))


class CreateOrderSchema(Schema):
    customer_id = fields.UUID(required=False, allow_none=True, data_key="customerId")
    new_customer_name = fields.String(required=False, allow_none=True, data_key="newCustomerName", validate=validate.Length(max=200))
    new_customer_phone = fields.String(required=False, allow_none=True, data_key="newCustomerPhone", validate=validate.Length(max=20))
    items = fields.List(fields.Nested(CreateOrderLineItemSchema), required=True, validate=validate.Length(min=1))
    notes = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))
    id = fields.UUID(required=False, allow_none=True)


class DeleteReasonSchema(Schema):
    reason = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))


class CancelOrderSchema(Schema):
    reason = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))


class AutoClearDurationField(fields.String):
    """Restricts to the presets the frontend actually offers -- Off, 5
    min, 15 min, or Custom (which additionally requires customHours)."""

    def __init__(self, **kwargs):
        super().__init__(validate=validate.OneOf(["OFF", "5_MIN", "15_MIN", "CUSTOM"]), **kwargs)


class SetAutoClearSettingSchema(Schema):
    scope = fields.String(required=True, validate=validate.OneOf(["COMPLETED", "CANCELLED"]))
    duration = AutoClearDurationField(required=True)
    custom_hours = fields.Float(required=False, allow_none=True, data_key="customHours", validate=validate.Range(min=0.01))
