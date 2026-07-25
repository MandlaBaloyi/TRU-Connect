"""
OTP generation and hashing helpers.
Ref: continuation master prompt (Phase 3), Step 13.

Kept separate from src/utils/security.py (which is specifically password
hashing/complexity) since OTP codes use a different, deliberately
different hashing approach -- see the design note in
src/models/otp_verification.py for why sha256 rather than bcrypt is used
here.
"""
from __future__ import annotations

import hashlib
import secrets


def generate_numeric_otp(length: int = 6) -> str:
    """Cryptographically random numeric OTP (uses `secrets`, not
    `random` -- `random` is not safe for anything security-sensitive)."""
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def verify_otp_hash(code: str, code_hash: str) -> bool:
    return hash_otp(code) == code_hash


def generate_reset_token() -> str:
    """Cryptographically random, URL-safe password reset token (Step 14:
    "Secure reset tokens" -- must be unguessable, unlike a 6-digit OTP)."""
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
