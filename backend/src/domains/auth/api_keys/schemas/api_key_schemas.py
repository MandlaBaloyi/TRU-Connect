"""
API key request schemas.

Only the CREATE call has a body worth validating -- listing and revoking
are addressed by URL. Validation here is shape-only (is this a string,
is this a list); what a scope MEANS and whether the account may have
another key are business rules and live in the service, so they hold no
matter who calls it.
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate


class CreateApiKeySchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=80))

    # Not validated against the vocabulary here on purpose. The service
    # rejects unknown scopes by NAME ("Unknown permissions:
    # catalogue:wrote"), which is the message that actually fixes the
    # caller's typo -- a Marshmallow OneOf would flatten that into a
    # generic field error and would also mean the scope list is spelled
    # out in two files that can drift apart.
    scopes = fields.List(fields.String(), required=True)

    # Optional. Absent means "no expiry", which is the normal case for a
    # running integration -- see the model's expires_at comment.
    expires_in_days = fields.Integer(required=False, allow_none=True, load_default=None)
