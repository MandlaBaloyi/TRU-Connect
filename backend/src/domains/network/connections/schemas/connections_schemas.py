"""
network/connections request schemas. Search and connection-
request routes never needed one (a query param, and a body-less POST
respectively) -- Network Invitation is the first endpoint in this
domain that actually needs to validate a request body, hence this
file existing now rather than from the start.
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate


class InviteContactSchema(Schema):
    """Shared by both invitation directions -- invite_supplier and
    invite_business (api/connections_routes.py) both take
    exactly this shape (an email, nothing role-specific), so one
    schema serves both rather than two identical copies."""

    email = fields.Email(required=True)


class EndConnectionSchema(Schema):
    reason = fields.Str(
        required=True,
        validate=validate.OneOf(["FOUND_BETTER_SUPPLIER", "NO_LONGER_NEEDED", "BAD_EXPERIENCE", "OTHER"]),
    )
    details = fields.Str(required=False, allow_none=True, load_default=None)


class ReportSupplierSchema(Schema):
    reason = fields.Str(
        required=True,
        validate=validate.OneOf(
            ["FAKE_PRODUCTS", "SUSPECTED_SCAM", "ORDER_NOT_RECEIVED", "INAPPROPRIATE_CONTENT", "OTHER"]
        ),
    )
    details = fields.Str(required=False, allow_none=True, load_default=None)
    # Set when reported from a specific product's own 3-dot menu,
    # omitted when reported from the catalogue's own menu -- the
    # service layer verifies this genuinely belongs to the supplier in
    # the URL before trusting it (see report_supplier's own
    # docstring), so this schema only validates SHAPE (a real UUID
    # string), not ownership.
    product_id = fields.Str(required=False, allow_none=True, load_default=None)
