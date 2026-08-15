"""
network/connections request schemas. Search and connection-
request routes never needed one (a query param, and a body-less POST
respectively) -- Network Invitation is the first endpoint in this
domain that actually needs to validate a request body, hence this
file existing now rather than from the start.
"""
from __future__ import annotations

from marshmallow import Schema, fields


class InviteContactSchema(Schema):
    """Shared by both invitation directions -- invite_supplier and
    invite_business (api/connections_routes.py) both take
    exactly this shape (an email, nothing role-specific), so one
    schema serves both rather than two identical copies."""

    email = fields.Email(required=True)
