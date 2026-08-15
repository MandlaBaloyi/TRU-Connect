"""
Authentication request schemas.
 (Registration);
RULES_AND_WORKFLOWS.txt, Sections 1-2.

Field names use data_key to match the mobile app's camelCase wire format
(frontend/mobile/src/features/auth/types.ts) exactly -- see the
integration note in this generator's docstring for why confirm_password
and accept_privacy_policy/accept_terms are validated here even though
the mobile client already checks them; server-side validation cannot
rely on a client that could be bypassed.
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate, validates, validates_schema
from marshmallow import ValidationError as MarshmallowValidationError

from src.shared.security.security import validate_password_complexity


class BusinessRegisterSchema(Schema):
    first_name = fields.String(required=True, data_key="firstName", validate=validate.Length(min=1, max=100))
    last_name = fields.String(required=True, data_key="lastName", validate=validate.Length(min=1, max=100))
    business_name = fields.String(
        required=False, allow_none=True, data_key="businessName", validate=validate.Length(max=255)
    )
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    confirm_password = fields.String(required=True, load_only=True, data_key="confirmPassword")
    accept_privacy_policy = fields.Boolean(required=True, data_key="acceptPrivacyPolicy")
    # Supplier Invitation, reverse direction (file.txt Phase 2) --
    # present only when this registration was reached via a supplier's
    # invitation link. Same optional, never-blocks-registration
    # reasoning as SupplierRegisterSchema's own invitation_ticket.
    invitation_ticket = fields.String(required=False, allow_none=True, data_key="invitationTicket")

    @validates("password")
    def validate_password_strength(self, value, **kwargs):
        errors = validate_password_complexity(value)
        if errors:
            raise MarshmallowValidationError(errors)

    @validates_schema
    def validate_cross_fields(self, data, **kwargs):
        if data.get("password") != data.get("confirm_password"):
            raise MarshmallowValidationError("Passwords do not match.", field_name="confirm_password")
        if not data.get("accept_privacy_policy"):
            raise MarshmallowValidationError(
                "You must accept the Privacy Policy.", field_name="accept_privacy_policy"
            )


class SupplierRegisterSchema(Schema):
    owner_name = fields.String(required=True, data_key="ownerName", validate=validate.Length(min=1, max=200))
    business_name = fields.String(
        required=False, allow_none=True, data_key="businessName", validate=validate.Length(max=255)
    )
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    confirm_password = fields.String(required=True, load_only=True, data_key="confirmPassword")
    accept_terms = fields.Boolean(required=True, data_key="acceptTerms")
    # Supplier Invitation (file.txt Phase 2) -- present only when this
    # registration was reached via an invitation link/deep link.
    # Optional and load_only-adjacent (never echoed back): a missing or
    # invalid ticket never blocks registration itself, see
    # connections_service.link_invitation_at_registration's own
    # docstring for why that's a silent no-op, not a validation error.
    invitation_ticket = fields.String(required=False, allow_none=True, data_key="invitationTicket")

    @validates("password")
    def validate_password_strength(self, value, **kwargs):
        errors = validate_password_complexity(value)
        if errors:
            raise MarshmallowValidationError(errors)

    @validates_schema
    def validate_cross_fields(self, data, **kwargs):
        if data.get("password") != data.get("confirm_password"):
            raise MarshmallowValidationError("Passwords do not match.", field_name="confirm_password")
        if not data.get("accept_terms"):
            raise MarshmallowValidationError("You must accept the Terms.", field_name="accept_terms")


class LoginSchema(Schema):
    """Matches frontend/mobile SignInPayload exactly (email + password
    only -- rememberMe is intentionally not sent by the mobile client)."""

    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
