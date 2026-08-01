"""
OTP generation and hashing helpers.
Ref: continuation master prompt (Phase 3), Step 13.

Reset-ticket generation/hashing (generate_reset_token / hash_reset_token)
moved to src/shared/tickets.py (Auth Hardening master prompt,
Objectives 5/8) -- this file is OTP-specific only, avoiding two parallel
implementations of "generate a random secret and hash it".
"""
from __future__ import annotations

import hashlib
import hmac
import secrets


def generate_numeric_otp(length: int = 6) -> str:
    """Cryptographically random numeric OTP (uses `secrets`, not
    `random` -- `random` is not safe for anything security-sensitive)."""
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def verify_otp_hash(code: str, code_hash: str) -> bool:
    """Constant-time comparison (Auth Hardening master prompt,
    Objective 9)."""
    return hmac.compare_digest(hash_otp(code), code_hash)
