"""
Unified Secure Ticket Service.
 Auth Hardening 

SCOPE (deliberate, documented boundary)
----------------------------------------
This module provides the CRYPTOGRAPHIC PRIMITIVES every secure,
single-use, expiring URL should use: generation, hashing, constant-time
verification, and expiry helpers.

It does NOT own storage. A generic multi-purpose "tickets" database table
was considered and rejected for now: today there is exactly one real use
case (password reset), and migrating the already-implemented and
already-migrated password_reset_tokens table into a generic structure
would be schema churn with no present benefit. When a second real use
case exists (supplier invitation, magic login, etc.), each domain adds
its own lightweight table storing a ticket_hash produced by this module
-- consistent with how every other domain in this codebase owns its own
storage. What is shared, and what actually matters for security, is the
generation/hashing/verification logic itself, so it is never
reimplemented ad hoc per feature.

WHY SHA-256, NOT BCRYPT
------------------------
Unlike passwords, tickets are high-entropy (256 bits from
token_urlsafe(32)) and single-use/short-lived. bcrypt's deliberate
slowness buys negligible extra protection here, at real cost to
legitimate verification latency. A fast hash is the correct tool for
this job -- the entropy of the ticket itself is what makes it
unguessable, not the hash function's speed.

WHY LOOKUP-BY-HASH IS SAFE WITHOUT AN EXTRA CONSTANT-TIME COMPARE
--------------------------------------------------------------------
Every caller of this module looks up a stored record BY its hash (a
database index equality lookup), rather than fetching a candidate record
and then comparing hashes in application code. Looking a row up by an
indexed hash column is the standard, accepted-secure pattern used by
virtually every framework for this exact scenario -- there is no
meaningful timing side-channel to defend against here the way there is
when comparing two attacker-influenced strings character by character in
Python. verify_ticket() below is provided for the rare case a caller
already has both values in hand and wants an explicit constant-time
check.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from src.core.base_model import utcnow


def create_ticket() -> str:
    """Generates a new cryptographically random, URL-safe ticket value.
    This is the value that goes into a URL/email, e.g.
    https://.../reset-password?ticket=<this>. NEVER store this value
    directly -- store only hash_ticket(this)."""
    return secrets.token_urlsafe(32)


def hash_ticket(raw_ticket: str) -> str:
    """One-way hash of a ticket, for storage."""
    return hashlib.sha256(raw_ticket.encode("utf-8")).hexdigest()


def verify_ticket(raw_ticket: str, stored_hash: str) -> bool:
    """Constant-time comparison, for callers that already have both the
    presented ticket and the stored hash in hand (rather than looking a
    row up BY hash, which is what every current caller in this codebase
    does instead -- see the module docstring)."""
    return hmac.compare_digest(hash_ticket(raw_ticket), stored_hash)


def ticket_expiry(minutes: int = 0, hours: int = 0, days: int = 0) -> datetime:
    """Convenience helper so every ticket-issuing service computes
    expires_at the same way."""
    return utcnow() + timedelta(minutes=minutes, hours=hours, days=days)


def is_ticket_expired(expires_at: datetime) -> bool:
    return expires_at <= utcnow()
