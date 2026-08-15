"""
OTP request/verification schemas.
matches frontend/mobile/src/features/auth/types.ts (VerifyOtpPayload: destination
+ code) 
(/auth/phone/request-otp, /auth/phone/verify-otp).
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate


class RequestOtpSchema(Schema):
    destination = fields.String(required=True, validate=validate.Length(min=1, max=255))


class VerifyOtpSchema(Schema):
    destination = fields.String(required=True, validate=validate.Length(min=1, max=255))
    code = fields.String(required=True, validate=validate.Length(equal=6))
