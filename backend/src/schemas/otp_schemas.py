"""
OTP request/verification schemas.
Ref: continuation master prompt (Phase 3), Step 13; matches
frontend/mobile/src/features/auth/types.ts (VerifyOtpPayload: destination
+ code) and docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.1
(/auth/phone/request-otp, /auth/phone/verify-otp).
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate


class RequestOtpSchema(Schema):
    destination = fields.String(required=True, validate=validate.Length(min=1, max=255))


class VerifyOtpSchema(Schema):
    destination = fields.String(required=True, validate=validate.Length(min=1, max=255))
    code = fields.String(required=True, validate=validate.Length(equal=6))
