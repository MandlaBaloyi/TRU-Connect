"""
Forgot/Reset password schemas.
Ref: continuation master prompt (Phase 3), Step 14; Auth Hardening master
prompt, Objective 7 (field renamed "token" -> "ticket", matching the
external URL/API naming; no change to the underlying database column).
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate, validates, validates_schema
from marshmallow import ValidationError as MarshmallowValidationError

from src.shared.security.security import validate_password_complexity


class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    ticket = fields.String(required=True)
    new_password = fields.String(required=True, load_only=True, data_key="newPassword")
    confirm_password = fields.String(required=True, load_only=True, data_key="confirmPassword")

    @validates("new_password")
    def validate_password_strength(self, value, **kwargs):
        errors = validate_password_complexity(value)
        if errors:
            raise MarshmallowValidationError(errors)

    @validates_schema
    def validate_cross_fields(self, data, **kwargs):
        if data.get("new_password") != data.get("confirm_password"):
            raise MarshmallowValidationError("Passwords do not match.", field_name="confirm_password")


class ValidateResetTicketSchema(Schema):
    ticket = fields.String(required=True, validate=validate.Length(min=1))
