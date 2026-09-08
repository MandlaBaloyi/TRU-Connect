"""
shared/checkout request schemas -- same "validate SHAPE here, business
rules in the service layer" split as every other domain's own schemas
file (e.g. network/connections/schemas/connections_schemas.py).
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate


class AddCartItemSchema(Schema):
    product_id = fields.UUID(required=True, data_key="productId")
    quantity = fields.Int(required=True, validate=validate.Range(min=1))


class UpdateCartItemSchema(Schema):
    quantity = fields.Int(required=True, validate=validate.Range(min=1))


class SubmitCheckoutSchema(Schema):
    # validate.OneOf intentionally lists ALL FOUR real enum values,
    # not just the two checkout_service currently accepts (CASH,
    # PROOF_OF_PAYMENT) -- this schema only validates SHAPE (a real,
    # spelled-correctly payment method), never availability. Rejecting
    # PAYFAST as "not yet available" is checkout_service's own job
    # (PaymentMethodNotAvailableError), so a business asking for it
    # gets a clear, specific "not available yet" message instead of a
    # generic "invalid value" one that would be misleading (PAYFAST is
    # a genuinely valid payment method on this platform, just not a
    # reachable choice in this pass).
    payment_method = fields.Str(
        required=True, data_key="paymentMethod", validate=validate.OneOf(["DIRECT", "CASH", "PROOF_OF_PAYMENT", "PAYFAST"])
    )
    delivery_type = fields.Str(required=True, data_key="deliveryType", validate=validate.OneOf(["DELIVER", "COLLECT"]))
    delivery_address_text = fields.Str(
        required=False, allow_none=True, load_default=None, data_key="deliveryAddressText"
    )
    # Structured companions to delivery_address_text -- all optional,
    # same reasoning as that field itself: COLLECT orders never send
    # any of these (the supplier's own address applies instead), and
    # even a DELIVER order predating this feature's frontend rollout
    # should keep working with only the free-text field populated.
    delivery_building = fields.Str(required=False, allow_none=True, load_default=None, data_key="deliveryBuilding")
    delivery_street = fields.Str(required=False, allow_none=True, load_default=None, data_key="deliveryStreet")
    delivery_suburb = fields.Str(required=False, allow_none=True, load_default=None, data_key="deliverySuburb")
    delivery_city = fields.Str(required=False, allow_none=True, load_default=None, data_key="deliveryCity")
    delivery_province = fields.Str(required=False, allow_none=True, load_default=None, data_key="deliveryProvince")
    delivery_postal_code = fields.Str(
        required=False, allow_none=True, load_default=None, data_key="deliveryPostalCode"
    )
    delivery_latitude = fields.Float(required=False, allow_none=True, load_default=None, data_key="deliveryLatitude")
    delivery_longitude = fields.Float(
        required=False, allow_none=True, load_default=None, data_key="deliveryLongitude"
    )
