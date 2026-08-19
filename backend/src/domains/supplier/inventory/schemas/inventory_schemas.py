"""
inventory request schemas -- shape validation only, business rules
stay in inventory_service.py, same split as products' own schemas.
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate

_REASON_VALUES = ["STOCK_RECEIVED", "STOCK_SOLD", "DAMAGED", "RETURNED", "MANUAL_ADJUSTMENT"]
_CHANNEL_VALUES = ["IN_APP", "EMAIL"]


class AdjustStockSchema(Schema):
    quantity_delta = fields.Integer(required=True)
    reason = fields.Str(required=True, validate=validate.OneOf(_REASON_VALUES))


class SetThresholdSchema(Schema):
    low_stock_threshold = fields.Integer(required=True, validate=validate.Range(min=0))


class UpdateSettingsSchema(Schema):
    default_low_stock_threshold = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=0))
    low_stock_alert_channel = fields.Str(required=False, allow_none=True, validate=validate.OneOf(_CHANNEL_VALUES))
