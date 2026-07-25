"""
OTP Repository.
Ref: continuation master prompt -- repositories ONLY talk to SQLAlchemy;
expiry/attempt/reuse business rules live in src/services/otp_service.py.
"""
from __future__ import annotations

from typing import Optional

from src.extensions import db
from src.models.otp_verification import OTPPurpose, OTPVerification


class OTPRepository:
    @staticmethod
    def create(user_id, purpose: OTPPurpose, destination: str, otp_code_hash: str, expires_at) -> OTPVerification:
        record = OTPVerification(
            user_id=user_id,
            purpose=purpose,
            destination=destination,
            otp_code_hash=otp_code_hash,
            expires_at=expires_at,
        )
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def get_latest_active(user_id, purpose: OTPPurpose) -> Optional[OTPVerification]:
        """Most recent, not-yet-used OTP for this user/purpose --
        requesting a new OTP does not delete older ones, but only the
        latest is ever considered valid for verification."""
        return (
            OTPVerification.query.filter_by(
                user_id=user_id, purpose=purpose, is_used=False, is_deleted=False
            )
            .order_by(OTPVerification.created_at.desc())
            .first()
        )

    @staticmethod
    def increment_attempts(record: OTPVerification) -> OTPVerification:
        record.attempts += 1
        db.session.commit()
        return record

    @staticmethod
    def mark_used(record: OTPVerification) -> OTPVerification:
        record.is_used = True
        db.session.commit()
        return record
