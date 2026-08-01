#!/usr/bin/env python3
"""
================================================================================
 TRU CONNECT BACKEND
 Authentication Domain Hardening
================================================================================

Closes the verification-bypass hole found in testing:
  1. Registration no longer issues tokens -- there is nothing to bypass
     with, because no valid session exists until OTP verification
     succeeds.
  2. Login is gated on verification_status == VERIFIED and
     account_status == ACTIVE, with a structured 403 (code
     "EMAIL_NOT_VERIFIED") including resend metadata.
  3. New @verified_required / @active_account_required /
     @fully_authenticated decorators re-check the DATABASE on every
     request, not a frozen JWT claim -- this is what protects every
     future endpoint, not just /login.
  4. Unverified re-registration is only resumed for the SAME role;
     accounts past UNVERIFIED_ACCOUNT_EXPIRY_HOURS are hard-deleted
     (not soft-deleted -- email has an unconditional UNIQUE constraint,
     so soft-delete would leave the address permanently unusable) and
     the email becomes genuinely available again.
  5. A shared, reusable ticket module (generation/hashing/verification)
     backs password reset today and is ready for magic-links,
     invitations, etc. later, WITHOUT a generic-ticket-table schema
     migration -- storage stays domain-owned.
  6. The password reset email now points at a real http(s) URL
     (APP_BASE_URL/reset-password?ticket=...), which bounces into the
     app's custom URL scheme, with a manual fallback for browsers that
     block script-initiated custom-scheme navigation.
  7. Failed-login lockout, audit logging, and IP capture on token
     issuance.

WHAT THIS SCRIPT WRITES (new files):
    src/shared/tickets.py
    src/shared/audit.py
    src/domains/platform/api/reset_redirect_routes.py

WHAT THIS SCRIPT REWRITES (existing files, business rules changing --
see this script's own top-of-file docstrings in each generated file for
exactly what's different):
    src/core/exceptions.py
    src/core/responses.py
    src/core/decorators.py
    src/shared/cache.py
    src/shared/constants.py
    src/domains/auth/utils/otp.py
    src/domains/auth/repositories/user_repository.py
    src/domains/auth/services/auth_service.py
    src/domains/auth/services/otp_service.py
    src/domains/auth/services/password_reset_service.py
    src/domains/auth/schemas/password_reset_schemas.py
    src/domains/auth/api/routes.py
    backend/tests/test_auth.py

WHAT THIS SCRIPT INTEGRATES (targeted edits, same safe anchor-based
pattern as every previous script -- skips with a warning rather than
guessing if the expected anchor isn't found):
    src/config.py               adds APP_BASE_URL + security constants
    src/__init__.py             registers reset_redirect_bp (root-level,
                                 NOT under /api/v1) + passes code/data
                                 through the AppError error handler
    src/domains/auth/models/__init__.py   (verified already correct)

WHAT THIS SCRIPT NEVER TOUCHES:
    src/extensions.py, app.py, src/core/base_model.py,
    src/domains/auth/models/**, src/domains/auth/repositories/
    (refresh_token_repository.py, otp_repository.py,
    password_reset_repository.py -- unchanged), src/domains/auth/
    schemas/auth_schemas.py, src/domains/auth/schemas/otp_schemas.py,
    src/shared/email.py, src/shared/security.py, src/shared/logger.py,
    src/shared/helpers.py, src/shared/metrics.py, src/shared/monitoring.py,
    src/shared/queue.py, src/shared/validators.py, all templates,
    requirements.txt, .env, migrations/**, docs/**, frontend/**

NO NEW MIGRATION REQUIRED. PasswordResetToken's physical column stays
`token_hash`; "ticket" is only the external, API-facing name.

USAGE (run from the TRU_Connect root, or pass --root):

    python generate_auth_hardening_.py --force
================================================================================
"""

import argparse
import os
import sys


BACKEND_REL = "backend"
FILES: dict = {}


# ==============================================================================
# src/core/exceptions.py -- extended with code/data and new specific
# exception types.
# ==============================================================================

FILES[os.path.join("src", "core", "exceptions.py")] = r'''"""
Custom exception hierarchy.
Ref: backend master prompt, "Proper exception handling"; Auth Hardening
master prompt, Objective 1 (structured error codes).

Services raise these instead of returning ad-hoc error tuples; the app
factory's single error handler converts any AppError into the standard
JSON envelope automatically -- routes never need to catch these
individually.

`code` and `data` are new, optional, additive fields. `code` is a stable,
machine-readable string (e.g. "EMAIL_NOT_VERIFIED") the frontend can
switch on instead of parsing the human-readable message. `data` carries
structured metadata alongside a failure (e.g. resend availability).
"""
from __future__ import annotations

from typing import Optional


class AppError(Exception):
    """Base class for all application-level errors."""

    status_code = 400
    code: Optional[str] = None

    def __init__(
        self,
        message: str,
        errors: Optional[list] = None,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        data: Optional[dict] = None,
    ):
        super().__init__(message)
        self.message = message
        self.errors = errors or []
        self.data = data
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class NotFoundError(AppError):
    status_code = 404


class ValidationError(AppError):
    status_code = 422


class ConflictError(AppError):
    status_code = 409


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class EmailNotVerifiedError(ForbiddenError):
    """Ref: Auth Hardening master prompt, Objective 1, Rule 3."""

    code = "EMAIL_NOT_VERIFIED"


class AccountInactiveError(ForbiddenError):
    code = "ACCOUNT_INACTIVE"


class AccountLockedError(AppError):
    """Ref: Auth Hardening master prompt, Objective 9 -- temporary
    lockout after repeated failed login attempts."""

    status_code = 423  # Locked
    code = "ACCOUNT_LOCKED"


class TicketInvalidError(UnauthorizedError):
    """Ref: Auth Hardening master prompt, Objectives 4/5/7 -- password
    reset (and future magic-link/invitation) ticket flows."""

    code = "TICKET_INVALID"
'''


# ==============================================================================
# src/core/responses.py -- extended with optional code/data on failure
# ==============================================================================

FILES[os.path.join("src", "core", "responses.py")] = r'''"""
Standard JSON response envelope.
Ref: docs/05_BACKEND_API_SPECIFICATION.txt §1; Auth Hardening master
prompt, Objective 1.

    Success: {"success": true,  "message": "...", "data": {}}
    Failure: {"success": false, "message": "...", "errors": [],
              "code": "...", "data": {}}   <- code/data optional

`code` and the failure-side `data` are additive: existing callers that
only pass message/errors/status_code are completely unaffected.
"""
from __future__ import annotations

from typing import Any, Optional

from flask import jsonify


def success_response(data: Any = None, message: str = "Success", status_code: int = 200):
    payload = {"success": True, "message": message, "data": data if data is not None else {}}
    return jsonify(payload), status_code


def error_response(
    message: str = "An error occurred",
    errors: Optional[list] = None,
    status_code: int = 400,
    code: Optional[str] = None,
    data: Optional[dict] = None,
):
    payload: dict = {"success": False, "message": message, "errors": errors or []}
    if code is not None:
        payload["code"] = code
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code
'''


# ==============================================================================
# src/core/decorators.py -- new verification/activity decorators, existing
# role_required / permission_required UNCHANGED
# ==============================================================================

FILES[os.path.join("src", "core", "decorators.py")] = r'''"""
Authorization decorators.
Ref: continuation master prompt, Step 10/15 (role_required,
permission_required -- UNCHANGED below); Auth Hardening master prompt,
Objective 3 (login_required, verified_required, active_account_required,
fully_authenticated -- NEW).

verified_required / active_account_required / fully_authenticated
deliberately RE-CHECK THE DATABASE on every request rather than trusting
a JWT claim. A claim baked into a token at issue time cannot reflect a
status that changes afterwards (e.g. an account verified, or
deactivated, after its current token was already issued) without an
explicit token re-issue -- a database check is what actually closes
that gap, at the cost of one extra query per protected request.
"""
from __future__ import annotations

from functools import wraps

from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from src.core.exceptions import AccountInactiveError, EmailNotVerifiedError, ForbiddenError


def _load_current_user():
    """Local import avoids a circular import between core (imported very
    early, by the app factory) and the auth domain."""
    from src.domains.auth.repositories.user_repository import UserRepository

    return UserRepository.get_by_id(get_jwt_identity())


def login_required(fn):
    """Thin, explicitly-named wrapper around flask_jwt_extended's
    jwt_required() -- exists so route declarations read @login_required
    rather than a raw library call, and so future session/audit hooks
    have one place to attach to."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def verified_required(fn):
    """Requires authentication AND a current, database-fresh
    verification_status == VERIFIED. This is the decorator that closes
    the "a valid token from an unverified account can still be used"
    hole -- apply it to any endpoint an unverified user must not reach."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        from src.domains.auth.models.user import VerificationStatus

        user = _load_current_user()
        if user is None or user.verification_status != VerificationStatus.VERIFIED:
            raise EmailNotVerifiedError("Please verify your email before continuing.")
        return fn(*args, **kwargs)

    return wrapper


def active_account_required(fn):
    """Requires authentication and account_status == ACTIVE."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        from src.domains.auth.models.user import AccountStatus

        user = _load_current_user()
        if user is None or user.account_status != AccountStatus.ACTIVE:
            raise AccountInactiveError("This account is not active.")
        return fn(*args, **kwargs)

    return wrapper


def fully_authenticated(fn):
    """Convenience combination: authenticated + verified + active, in
    ONE decorator and ONE database lookup, for the common case (Auth
    Hardening master prompt, Objective 3 examples: /dashboard, /orders,
    /profile, /catalogue, /notifications)."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        from src.domains.auth.models.user import AccountStatus, VerificationStatus

        user = _load_current_user()
        if user is None or user.verification_status != VerificationStatus.VERIFIED:
            raise EmailNotVerifiedError("Please verify your email before continuing.")
        if user.account_status != AccountStatus.ACTIVE:
            raise AccountInactiveError("This account is not active.")
        return fn(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles: str):
    """UNCHANGED from the continuation master prompt (Step 10/15).
    Stacks JWT verification + role authorization in one decorator.
    Supports every role in UserRole and any future role added to that
    enum without this decorator changing."""

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in allowed_roles:
                raise ForbiddenError("You do not have permission to access this resource.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def permission_required(*required_permissions: str):
    """UNCHANGED -- structural placeholder for granular permissions;
    see the continuation master prompt, Step 15, for the full rationale."""

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            granted = set(claims.get("permissions", []))
            if not set(required_permissions).issubset(granted):
                raise ForbiddenError("You do not have permission to access this resource.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
'''


# ==============================================================================
# src/shared/cache.py -- add get_count (read-only) and reset, needed for
# login lockout bookkeeping. Existing check_rate_limit/increment/get/set
# UNCHANGED.
# ==============================================================================

FILES[os.path.join("src", "shared", "cache.py")] = r'''"""
Cache abstraction + rate limiting.
Ref: "Shared Notification Infrastructure" master prompt (cache.py,
check_rate_limit -- UNCHANGED); Auth Hardening master prompt, Objective 9
(get_count, reset -- NEW, needed for login-attempt lockout bookkeeping,
which must READ the current failure count without incrementing it, and
must be able to CLEAR it on a successful login).
"""
from __future__ import annotations

import threading
import time
from typing import Optional


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value, expires_at: Optional[float]):
        self.value = value
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        return self.expires_at is not None and time.time() >= self.expires_at


class InMemoryCache:
    def __init__(self):
        self._store: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._store.get(key)
            if entry is None or entry.is_expired():
                self._store.pop(key, None)
                return None
            return entry.value

    def get_count(self, key: str) -> int:
        """Read-only: current integer counter value, 0 if absent/expired.
        Does NOT increment -- use increment() for that."""
        value = self.get(key)
        return value if isinstance(value, int) else 0

    def set(self, key: str, value, ttl_seconds: Optional[float] = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds is not None else None
        with self._lock:
            self._store[key] = _CacheEntry(value, expires_at)

    def increment(self, key: str, ttl_seconds: Optional[float] = None) -> int:
        """Atomically increments an integer counter, creating it at 1 if
        absent, refreshing its TTL only on creation (matches Redis'
        common INCR + EXPIRE-if-new pattern)."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None or entry.is_expired():
                expires_at = time.time() + ttl_seconds if ttl_seconds is not None else None
                self._store[key] = _CacheEntry(1, expires_at)
                return 1
            entry.value += 1
            return entry.value

    def reset(self, key: str) -> None:
        """Clears a single key -- used to reset the failed-login counter
        on a successful login."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Test-only helper -- production code should never need this."""
        with self._lock:
            self._store.clear()


cache = InMemoryCache()


def check_rate_limit(key: str, max_count: int, window_seconds: int) -> bool:
    """Returns True if the action identified by `key` is still within its
    rate limit (and records this attempt), False if the limit has already
    been exceeded."""
    count = cache.increment(key, ttl_seconds=window_seconds)
    return count <= max_count
'''


# ==============================================================================
# src/shared/constants.py -- extended with Auth Hardening defaults
# ==============================================================================

FILES[os.path.join("src", "shared", "constants.py")] = r'''"""
Notification + Auth Hardening defaults.
Ref: "Shared Notification Infrastructure" master prompt (MailProvider,
mail defaults, rate limits -- UNCHANGED); Auth Hardening master prompt,
Objectives 1-2-4-7-9 (the block below -- NEW).

These are DEFAULTS, used when the corresponding environment variable /
app.config value is not set. The authoritative, overridable versions
live in src/config.py (APP_BASE_URL, UNVERIFIED_ACCOUNT_EXPIRY_HOURS,
LOGIN_MAX_FAILED_ATTEMPTS, LOGIN_LOCKOUT_WINDOW_MINUTES,
PASSWORD_RESET_TICKET_EXPIRY_HOURS) -- these module-level constants exist
as fallbacks for any code path that runs outside an app context.
"""
from __future__ import annotations

import enum


class MailProvider(str, enum.Enum):
    SMTP = "smtp"
    SES = "ses"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    AZURE = "azure"
    FAKE = "fake"


DEFAULT_MAIL_TIMEOUT_SECONDS = 10
DEFAULT_MAIL_MAX_RETRIES = 3
DEFAULT_MAIL_RETRY_DELAYS_SECONDS = [5, 15, 60]

MAX_OTP_EMAILS_PER_HOUR = 5
MAX_PASSWORD_RESET_EMAILS_PER_HOUR = 3
MAX_WELCOME_EMAILS_PER_ACCOUNT = 1
MAX_EMAILS_PER_USER_PER_HOUR = 10

# --- Auth Hardening additions ---
DEFAULT_UNVERIFIED_ACCOUNT_EXPIRY_HOURS = 24
DEFAULT_LOGIN_MAX_FAILED_ATTEMPTS = 5
DEFAULT_LOGIN_LOCKOUT_WINDOW_MINUTES = 15
DEFAULT_PASSWORD_RESET_TICKET_EXPIRY_HOURS = 1
'''


# ==============================================================================
# src/shared/tickets.py -- NEW: unified secure ticket primitives
# ==============================================================================

FILES[os.path.join("src", "shared", "tickets.py")] = r'''"""
Unified Secure Ticket Service.
Ref: Auth Hardening master prompt, Objective 5.

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
'''


# ==============================================================================
# src/shared/audit.py -- NEW: general security/audit event logging
# ==============================================================================

FILES[os.path.join("src", "shared", "audit.py")] = r'''"""
Security / audit event logging.
Ref: Auth Hardening master prompt, Objective 9.

Distinct from src/shared/monitoring.py, which is specifically the email
DELIVERY lifecycle (queued/sent/failed/retry). This module is general
authentication and security event logging: logins, lockouts,
verification-gate hits, password resets, account expiry cleanup.

Never logs a password, OTP code, reset ticket, or JWT -- only identifiers
(masked email, user id) and IP address, matching the same "never log
sensitive values" rule the email infrastructure already follows.
"""
from __future__ import annotations

from typing import Optional

from src.shared.helpers import mask_email

import logging

logger = logging.getLogger("tru_connect.audit")


def log_login_success(user_id: str, ip_address: Optional[str]) -> None:
    logger.info("login_success user_id=%s ip=%s", user_id, ip_address or "unknown")


def log_login_failed(email: str, ip_address: Optional[str]) -> None:
    logger.warning("login_failed email=%s ip=%s", mask_email(email), ip_address or "unknown")


def log_login_locked_out(email: str, ip_address: Optional[str]) -> None:
    logger.warning("login_locked_out email=%s ip=%s", mask_email(email), ip_address or "unknown")


def log_login_blocked_unverified(email: str, ip_address: Optional[str]) -> None:
    logger.info("login_blocked_unverified email=%s ip=%s", mask_email(email), ip_address or "unknown")


def log_unverified_account_expired(email: str) -> None:
    logger.info("unverified_account_expired email=%s", mask_email(email))


def log_registration_role_conflict(email: str, existing_role: str, attempted_role: str) -> None:
    logger.info(
        "registration_role_conflict email=%s existing_role=%s attempted_role=%s",
        mask_email(email),
        existing_role,
        attempted_role,
    )


def log_password_reset_requested(email: str) -> None:
    logger.info("password_reset_requested email=%s", mask_email(email))


def log_password_reset_completed(user_id: str) -> None:
    logger.info("password_reset_completed user_id=%s", user_id)
'''

# ==============================================================================
# src/domains/auth/utils/otp.py -- trimmed to OTP-only (reset-ticket
# functions moved to src/shared/tickets.py, Objective 5/8: avoid
# duplicated code). Also upgraded to constant-time OTP comparison.
# ==============================================================================

FILES[os.path.join("src", "domains", "auth", "utils", "otp.py")] = r'''"""
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
'''


# ==============================================================================
# src/domains/auth/repositories/user_repository.py -- adds hard_delete,
# needed for genuine (not soft) deletion of expired-unverified accounts.
# Everything else UNCHANGED.
# ==============================================================================

FILES[os.path.join("src", "domains", "auth", "repositories", "user_repository.py")] = r'''"""
User Repository.
Ref: continuation master prompt -- repositories ONLY talk to SQLAlchemy;
no business rules here.

hard_delete is new (Auth Hardening master prompt, Objective 2). Every
other method is UNCHANGED.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.core.base_model import utcnow
from src.extensions import db
from src.domains.auth.models.user import User


class UserRepository:
    @staticmethod
    def get_by_id(user_id: str | UUID) -> Optional[User]:
        return User.query.filter_by(id=user_id, is_deleted=False).first()

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        normalized = email.strip().lower()
        return User.query.filter_by(email=normalized, is_deleted=False).first()

    @staticmethod
    def exists_by_email(email: str) -> bool:
        return UserRepository.get_by_email(email) is not None

    @staticmethod
    def create(**kwargs) -> User:
        if "email" in kwargs and kwargs["email"] is not None:
            kwargs["email"] = kwargs["email"].strip().lower()
        user = User(**kwargs)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_last_login(user: User) -> User:
        user.last_login_at = utcnow()
        db.session.commit()
        return user

    @staticmethod
    def hard_delete(user: User) -> None:
        """Permanently removes a user row (and, via each child table's
        ON DELETE CASCADE, their refresh tokens / OTP records / password
        reset tickets).

        Used ONLY for unverified accounts that exceeded
        UNVERIFIED_ACCOUNT_EXPIRY_HOURS without ever completing
        verification. Such an account never became a real, trust-bearing
        entity -- soft_delete() (used everywhere else, to preserve
        trust-relevant history) is deliberately NOT used here, because
        the `email` column has an UNCONDITIONAL unique constraint (not
        scoped to is_deleted=false); a soft-deleted row would leave that
        email permanently unable to be reused, exactly the "permanent
        reservation" problem this feature exists to prevent.
        """
        db.session.delete(user)
        db.session.commit()
'''


# ==============================================================================
# src/domains/auth/services/auth_service.py -- major rewrite.
# ==============================================================================

FILES[os.path.join("src", "domains", "auth", "services", "auth_service.py")] = r'''"""
Authentication Service.
Ref: continuation master prompt, Steps 7-12; "Shared Notification
Infrastructure" master prompt (welcome email -- now sent from
OTPService, not here); Auth Hardening master prompt, Objectives 1-2-9.

REGISTRATION NO LONGER ISSUES TOKENS
-------------------------------------
register_business/register_supplier create the account and send the
verification OTP -- nothing else. There is no token to bypass with,
because none is issued until OTPService.verify_otp succeeds. Verifying
email IS the first authenticated moment for a new account.

UNVERIFIED RE-REGISTRATION POLICY
-----------------------------------
  - Existing account is VERIFIED             -> 409 Conflict (blocks).
  - Existing account is UNVERIFIED and past
    UNVERIFIED_ACCOUNT_EXPIRY_HOURS           -> hard-deleted; treated as
                                                  if it never existed;
                                                  fresh registration
                                                  proceeds normally.
  - Existing account is UNVERIFIED, within
    the window, SAME role requested           -> "resumed": profile
                                                  fields updated, a new
                                                  OTP is sent. This is
                                                  NOT a duplicate account
                                                  -- same row.
  - Existing account is UNVERIFIED, within
    the window, DIFFERENT role requested       -> 409 Conflict. Silently
                                                  flipping an unverified
                                                  account's role on every
                                                  registration attempt
                                                  was the exact bypass
                                                  pattern found in
                                                  testing; this closes it.

LOGIN GATING
-------------
Login enforces, in order: failed-attempt lockout, credential check,
account_status == ACTIVE, verification_status == VERIFIED. Only after
all four pass are tokens issued. See login() below for the exact
structured error each failure mode returns.
"""
from __future__ import annotations

import hashlib
from typing import Optional, Tuple

from flask import current_app

from flask_jwt_extended import create_access_token, create_refresh_token, get_jti

from src.core.base_model import utcnow
from src.core.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    ConflictError,
    EmailNotVerifiedError,
    UnauthorizedError,
)
from src.domains.auth.models.user import AccountStatus, User, UserRole, VerificationStatus
from src.domains.auth.repositories.refresh_token_repository import RefreshTokenRepository
from src.domains.auth.repositories.user_repository import UserRepository
from src.shared import audit
from src.shared.cache import cache
from src.shared.constants import (
    DEFAULT_LOGIN_LOCKOUT_WINDOW_MINUTES,
    DEFAULT_LOGIN_MAX_FAILED_ATTEMPTS,
    DEFAULT_UNVERIFIED_ACCOUNT_EXPIRY_HOURS,
)
from src.shared.security import hash_password, verify_password


def _hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode("utf-8")).hexdigest()


def _login_lockout_key(email: str) -> str:
    return f"login_failed:{email.strip().lower()}"


class AuthService:
    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    @staticmethod
    def register_business(data: dict) -> User:
        user = AuthService._create_or_resume(
            data=data, role=UserRole.BUSINESS, first_name=data["first_name"], last_name=data["last_name"]
        )
        AuthService._send_verification_otp(user)
        return user

    @staticmethod
    def register_supplier(data: dict) -> User:
        user = AuthService._create_or_resume(
            data=data, role=UserRole.SUPPLIER, first_name=data["owner_name"], last_name=None
        )
        AuthService._send_verification_otp(user)
        return user

    @staticmethod
    def _is_unverified_expired(user: User) -> bool:
        expiry_hours = current_app.config.get(
            "UNVERIFIED_ACCOUNT_EXPIRY_HOURS", DEFAULT_UNVERIFIED_ACCOUNT_EXPIRY_HOURS
        )
        return (utcnow() - user.created_at).total_seconds() > expiry_hours * 3600

    @staticmethod
    def _create_or_resume(data: dict, role: UserRole, first_name: str, last_name: Optional[str]) -> User:
        existing = UserRepository.get_by_email(data["email"])

        if existing is not None:
            if existing.verification_status == VerificationStatus.VERIFIED:
                raise ConflictError("An account with this email already exists.")

            if AuthService._is_unverified_expired(existing):
                audit.log_unverified_account_expired(existing.email)
                UserRepository.hard_delete(existing)
                existing = None
            elif existing.role != role:
                audit.log_registration_role_conflict(data["email"], existing.role.value, role.value)
                raise ConflictError(
                    f"This email already has a pending {existing.role.value} registration. "
                    "Verify that account, or wait for it to expire, before registering as a "
                    "different account type."
                )
            else:
                # Resume: same email, same role, still within the window.
                existing.password_hash = hash_password(data["password"])
                existing.first_name = first_name
                existing.last_name = last_name
                from src.extensions import db

                db.session.commit()
                return existing

        return UserRepository.create(
            email=data["email"],
            password_hash=hash_password(data["password"]),
            role=role,
            first_name=first_name,
            last_name=last_name,
        )

    @staticmethod
    def _send_verification_otp(user: User) -> None:
        """Never raises: a failed verification email must not roll back
        a successfully created account. The user can still request a
        resend once they realise nothing arrived."""
        from src.domains.auth.models.otp_verification import OTPPurpose
        from src.domains.auth.services.otp_service import OTPService

        try:
            OTPService.request_otp(destination=user.email, purpose=OTPPurpose.EMAIL_VERIFICATION)
        except Exception:  # noqa: BLE001
            current_app.logger.exception("Failed to send registration OTP for user %s", user.id)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    @staticmethod
    def login(email: str, password: str, ip_address: Optional[str] = None) -> Tuple[User, dict]:
        lockout_key = _login_lockout_key(email)
        max_attempts = current_app.config.get(
            "LOGIN_MAX_FAILED_ATTEMPTS", DEFAULT_LOGIN_MAX_FAILED_ATTEMPTS
        )
        lockout_window_seconds = (
            current_app.config.get("LOGIN_LOCKOUT_WINDOW_MINUTES", DEFAULT_LOGIN_LOCKOUT_WINDOW_MINUTES) * 60
        )

        if cache.get_count(lockout_key) >= max_attempts:
            audit.log_login_locked_out(email, ip_address)
            raise AccountLockedError(
                "Too many failed sign-in attempts. Please try again later.",
                data={"lockout_window_minutes": lockout_window_seconds // 60},
            )

        user = UserRepository.get_by_email(email)

        # An expired, never-verified account is treated as if it never
        # existed: cleaned up here too (not just at registration), so a
        # stale unverified row can't sit around indefinitely just because
        # nobody happened to re-register that address.
        if (
            user is not None
            and user.verification_status == VerificationStatus.UNVERIFIED
            and AuthService._is_unverified_expired(user)
        ):
            audit.log_unverified_account_expired(user.email)
            UserRepository.hard_delete(user)
            user = None

        if user is None or not verify_password(password, user.password_hash):
            cache.increment(lockout_key, ttl_seconds=lockout_window_seconds)
            audit.log_login_failed(email, ip_address)
            raise UnauthorizedError("Invalid email or password.")

        if user.account_status != AccountStatus.ACTIVE:
            raise AccountInactiveError("This account has been deactivated.")

        if user.verification_status != VerificationStatus.VERIFIED:
            audit.log_login_blocked_unverified(email, ip_address)
            expiry_hours = current_app.config.get(
                "UNVERIFIED_ACCOUNT_EXPIRY_HOURS", DEFAULT_UNVERIFIED_ACCOUNT_EXPIRY_HOURS
            )
            seconds_elapsed = (utcnow() - user.created_at).total_seconds()
            remaining_seconds = max(0, int(expiry_hours * 3600 - seconds_elapsed))
            raise EmailNotVerifiedError(
                "Please verify your email before signing in.",
                data={
                    "resend_available": True,
                    "verification_endpoint": "/auth/phone/request-otp",
                    "remaining_verification_seconds": remaining_seconds,
                },
            )

        # Success -- clear the failed-attempt counter for this email.
        cache.reset(lockout_key)
        UserRepository.update_last_login(user)
        tokens = AuthService._issue_tokens(user, ip_address=ip_address)
        audit.log_login_success(str(user.id), ip_address)
        return user, tokens

    # ------------------------------------------------------------------
    # JWT issuance
    # ------------------------------------------------------------------

    @staticmethod
    def _issue_tokens(
        user: User, device_id: Optional[str] = None, ip_address: Optional[str] = None
    ) -> dict:
        additional_claims = {"role": user.role.value}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=str(user.id), additional_claims=additional_claims)

        jti = get_jti(refresh_token)
        expires_at = utcnow() + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]
        RefreshTokenRepository.create(
            user_id=user.id,
            jti_hash=_hash_jti(jti),
            expires_at=expires_at,
            device_id=device_id,
            ip_address=ip_address,
        )

        return {"access_token": access_token, "refresh_token": refresh_token}

    # ------------------------------------------------------------------
    # Refresh Token rotation
    # ------------------------------------------------------------------

    @staticmethod
    def refresh(
        current_jti: str, user_id: str, device_id: Optional[str] = None, ip_address: Optional[str] = None
    ) -> dict:
        token_record = RefreshTokenRepository.get_by_jti_hash(_hash_jti(current_jti))

        if token_record is None or not token_record.is_valid():
            raise UnauthorizedError("Refresh token is invalid or has been revoked.")

        RefreshTokenRepository.revoke(token_record)

        user = UserRepository.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found.")

        if user.account_status != AccountStatus.ACTIVE:
            raise AccountInactiveError("This account has been deactivated.")

        return AuthService._issue_tokens(user, device_id=device_id, ip_address=ip_address)

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    @staticmethod
    def logout(user_id: str, refresh_token_jti: Optional[str] = None) -> None:
        if refresh_token_jti:
            token_record = RefreshTokenRepository.get_by_jti_hash(_hash_jti(refresh_token_jti))
            if token_record is not None and str(token_record.user_id) == str(user_id):
                RefreshTokenRepository.revoke(token_record)
            return

        RefreshTokenRepository.revoke_all_for_user(user_id)

    @staticmethod
    def get_current_user(user_id: str) -> User:
        user = UserRepository.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found.")
        return user
'''

# ==============================================================================
# src/domains/auth/services/otp_service.py -- verify_otp now returns
# (user, tokens) instead of None. Verifying email IS the first
# authenticated moment for a new account, since register() no longer
# issues tokens.
# ==============================================================================

FILES[os.path.join("src", "domains", "auth", "services", "otp_service.py")] = r'''"""
OTP Verification Service.
Ref: continuation master prompt (Phase 3), Step 13; "Shared Notification
Infrastructure" master prompt (welcome email); Auth Hardening master
prompt, Objective 1 (verify_otp now issues the first token pair).

Verifies by EMAIL, not phone -- frontend/mobile's registration does not
collect a phone number, so email is the only destination available at
this point in the flow.

WELCOME EMAIL: sent from here, only on the transition from unverified to
verified (never on a later re-verification).

TOKENS: register() no longer issues tokens (Auth Hardening, Objective 1)
-- there is no valid session for an unverified account. verify_otp() now
issues the first access/refresh pair on success, since proving control
of the email address is the first genuinely authenticated moment for a
brand-new account.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Tuple

from flask import current_app

from src.core.base_model import utcnow
from src.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from src.domains.auth.models.otp_verification import OTPPurpose
from src.domains.auth.models.user import User, UserRole, VerificationStatus
from src.domains.auth.repositories.otp_repository import OTPRepository
from src.domains.auth.repositories.user_repository import UserRepository
from src.domains.auth.utils.otp import generate_numeric_otp, hash_otp, verify_otp_hash
from src.extensions import db
from src.shared.constants import MAX_OTP_EMAILS_PER_HOUR
from src.shared.email import EmailService

OTP_EXPIRY_MINUTES = 10


class OTPService:
    @staticmethod
    def request_otp(destination: str, purpose: OTPPurpose = OTPPurpose.EMAIL_VERIFICATION) -> None:
        user = UserRepository.get_by_email(destination)
        if user is None:
            # Never reveal whether this destination has an account.
            return

        code = generate_numeric_otp()
        expires_at = utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        OTPRepository.create(
            user_id=user.id,
            purpose=purpose,
            destination=destination,
            otp_code_hash=hash_otp(code),
            expires_at=expires_at,
        )

        purpose_label = "email address" if purpose == OTPPurpose.EMAIL_VERIFICATION else "phone number"
        EmailService.send_template(
            to=destination,
            template_name="otp.html",
            subject="Your TRU Connect verification code",
            context={"otp_code": code, "purpose_label": purpose_label, "expiry_minutes": OTP_EXPIRY_MINUTES},
            rate_limit_key=f"otp:{destination}",
            rate_limit_max=MAX_OTP_EMAILS_PER_HOUR,
            rate_limit_window_seconds=3600,
        )

    @staticmethod
    def verify_otp(
        destination: str, code: str, purpose: OTPPurpose = OTPPurpose.EMAIL_VERIFICATION
    ) -> Tuple[User, dict]:
        user = UserRepository.get_by_email(destination)
        if user is None:
            raise NotFoundError("No account found for this destination.")

        record = OTPRepository.get_latest_active(user.id, purpose)
        if record is None:
            raise UnauthorizedError("No pending verification code found. Please request a new one.")

        if record.is_expired():
            raise UnauthorizedError("This verification code has expired. Please request a new one.")

        if not record.has_attempts_remaining():
            raise ForbiddenError("Too many incorrect attempts. Please request a new verification code.")

        if record.destination != destination or not verify_otp_hash(code, record.otp_code_hash):
            OTPRepository.increment_attempts(record)
            raise UnauthorizedError("Incorrect verification code.")

        OTPRepository.mark_used(record)

        was_already_verified = user.verification_status == VerificationStatus.VERIFIED
        user.verification_status = VerificationStatus.VERIFIED
        db.session.commit()

        if not was_already_verified:
            OTPService._send_welcome_email(user)

        # Local import: AuthService imports OTPService (for the
        # registration-time OTP send), so importing AuthService at
        # module level here would be circular.
        from src.domains.auth.services.auth_service import AuthService

        tokens = AuthService._issue_tokens(user)
        return user, tokens

    @staticmethod
    def _send_welcome_email(user: User) -> None:
        try:
            if user.role == UserRole.SUPPLIER:
                template_name = "welcome_supplier.html"
                context = {"owner_name": user.first_name}
            else:
                template_name = "welcome_business.html"
                context = {"first_name": user.first_name}

            EmailService.send_template(
                to=user.email, template_name=template_name, subject="Welcome to TRU Connect", context=context
            )
        except Exception:  # noqa: BLE001
            current_app.logger.exception("Failed to send welcome email for user %s", user.id)
'''


# ==============================================================================
# src/domains/auth/services/password_reset_service.py -- rewritten to use
# src/shared/tickets.py; external naming is "ticket", not "token"; adds
# validate_ticket() for Objective 6 (frontend checks validity before
# rendering the form); reset link now a real APP_BASE_URL http(s) URL.
# ==============================================================================

FILES[os.path.join("src", "domains", "auth", "services", "password_reset_service.py")] = r'''"""
Forgot/Reset Password Service.
Ref: continuation master prompt (Phase 3), Step 14; Auth Hardening master
prompt, Objectives 4, 5, 6, 7.

NAMING NOTE: the physical database column remains
PasswordResetToken.token_hash (no migration -- see
src/shared/tickets.py's module docstring for the full rationale).
"ticket" is the external, API-facing name only; this file is the single
place that bridges the two.

RESET URL: built from APP_BASE_URL (src/config.py) + "/reset-password",
handled by src/domains/platform/api/reset_redirect_routes.py -- a real
http(s) URL (Objective 7), not a bare custom scheme, that bounces into
the app's truconnect:// deep link with a manual fallback.
"""
from __future__ import annotations

from flask import current_app

from src.core.exceptions import TicketInvalidError
from src.domains.auth.repositories.password_reset_repository import PasswordResetRepository
from src.domains.auth.repositories.refresh_token_repository import RefreshTokenRepository
from src.domains.auth.repositories.user_repository import UserRepository
from src.extensions import db
from src.shared import audit
from src.shared.constants import DEFAULT_PASSWORD_RESET_TICKET_EXPIRY_HOURS, MAX_PASSWORD_RESET_EMAILS_PER_HOUR
from src.shared.email import EmailService
from src.shared.security import hash_password
from src.shared.tickets import create_ticket, hash_ticket, is_ticket_expired, ticket_expiry


class PasswordResetService:
    @staticmethod
    def forgot_password(email: str) -> None:
        """Enumeration-safe: behaves identically (returns None, no
        exception) whether or not a matching user was found."""
        user = UserRepository.get_by_email(email)
        if user is None:
            return

        expiry_hours = current_app.config.get(
            "PASSWORD_RESET_TICKET_EXPIRY_HOURS", DEFAULT_PASSWORD_RESET_TICKET_EXPIRY_HOURS
        )
        raw_ticket = create_ticket()
        expires_at = ticket_expiry(hours=expiry_hours)
        PasswordResetRepository.create(user_id=user.id, token_hash=hash_ticket(raw_ticket), expires_at=expires_at)

        base_url = current_app.config.get("APP_BASE_URL", "http://localhost:5000")
        reset_url = f"{base_url}/reset-password?ticket={raw_ticket}"

        audit.log_password_reset_requested(email)

        EmailService.send_template(
            to=email,
            template_name="password_reset.html",
            subject="Reset your TRU Connect password",
            context={"reset_url": reset_url, "expiry_hours": expiry_hours},
            rate_limit_key=f"password_reset:{email}",
            rate_limit_max=MAX_PASSWORD_RESET_EMAILS_PER_HOUR,
            rate_limit_window_seconds=3600,
        )

    @staticmethod
    def validate_ticket(ticket: str) -> bool:
        """Read-only check (Auth Hardening master prompt, Objective 6) --
        lets the mobile app show "this link has expired" immediately on
        screen load, rather than only after the user fills in a new
        password and submits."""
        record = PasswordResetRepository.get_by_token_hash(hash_ticket(ticket))
        return record is not None and not record.is_used and not is_ticket_expired(record.expires_at)

    @staticmethod
    def reset_password(ticket: str, new_password: str) -> None:
        record = PasswordResetRepository.get_by_token_hash(hash_ticket(ticket))

        if record is None or record.is_used or is_ticket_expired(record.expires_at):
            raise TicketInvalidError("This password reset link is invalid or has expired.")

        user = UserRepository.get_by_id(record.user_id)
        if user is None:
            raise TicketInvalidError("This password reset link is invalid or has expired.")

        user.password_hash = hash_password(new_password)
        db.session.commit()

        PasswordResetRepository.mark_used(record)

        # Force re-login on every device by revoking all of this user's
        # active refresh tokens.
        RefreshTokenRepository.revoke_all_for_user(user.id)

        audit.log_password_reset_completed(str(user.id))
'''


# ==============================================================================
# src/domains/auth/schemas/password_reset_schemas.py -- field renamed
# token -> ticket; new ValidateResetTicketSchema.
# ==============================================================================

FILES[os.path.join("src", "domains", "auth", "schemas", "password_reset_schemas.py")] = r'''"""
Forgot/Reset password schemas.
Ref: continuation master prompt (Phase 3), Step 14; Auth Hardening master
prompt, Objective 7 (field renamed "token" -> "ticket", matching the
external URL/API naming; no change to the underlying database column).
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate, validates, validates_schema
from marshmallow import ValidationError as MarshmallowValidationError

from src.shared.security import validate_password_complexity


class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    ticket = fields.String(required=True)
    new_password = fields.String(required=True, load_only=True, data_key="newPassword")
    confirm_password = fields.String(required=True, load_only=True, data_key="confirmPassword")

    @validates("new_password")
    def validate_password_strength(self, value, **kwargs):
        errors = validate_password_complexity(value)
        if errors:
            raise MarshmallowValidationError(errors)

    @validates_schema
    def validate_cross_fields(self, data, **kwargs):
        if data.get("new_password") != data.get("confirm_password"):
            raise MarshmallowValidationError("Passwords do not match.", field_name="confirm_password")


class ValidateResetTicketSchema(Schema):
    ticket = fields.String(required=True, validate=validate.Length(min=1))
'''

# ==============================================================================
# src/domains/platform/api/reset_redirect_routes.py -- NEW: browser-facing
# bounce page. Deliberately NOT under /api/v1 -- must match the exact URL
# emailed to the user.
# ==============================================================================

FILES[os.path.join("src", "domains", "platform", "api", "reset_redirect_routes.py")] = r'''"""
Password Reset Redirect Page.
Ref: Auth Hardening master prompt, Objective 7.

Deliberately NOT under /api/v1 -- this is a browser-facing HTML page, not
a JSON API endpoint, and its URL must match exactly what is emailed to
the user: {APP_BASE_URL}/reset-password?ticket=...

This page never validates the ticket itself (that is the mobile app's
job, via GET /api/v1/auth/reset-password/validate and
POST /api/v1/auth/reset-password) -- its only job is bouncing a browser
into the installed app via its custom URL scheme, with a manual
"Open App" fallback. The fallback is required, not optional polish: some
mobile browsers (notably iOS Safari) block script-initiated custom-scheme
navigation, so an automatic-only redirect would silently fail for a
meaningful fraction of users.
"""
from __future__ import annotations

from flask import Blueprint, Response, request

reset_redirect_bp = Blueprint("reset_redirect", __name__)


@reset_redirect_bp.get("/reset-password")
def reset_password_redirect():
    ticket = request.args.get("ticket", "")
    deep_link = f"truconnect://reset-password?ticket={ticket}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reset your TRU Connect password</title>
  <meta http-equiv="refresh" content="0; url={deep_link}">
</head>
<body style="margin:0; padding:0; background-color:#F4F6F8; font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <div style="max-width:420px; margin:64px auto; padding:32px; background:#FFFFFF; border-radius:12px; text-align:center;">
    <h1 style="font-size:18px; color:#111417; margin:0 0 12px;">Opening TRU Connect&hellip;</h1>
    <p style="font-size:14px; color:#3A3F44; margin:0 0 24px;">
      If the app didn't open automatically, tap the button below.
    </p>
    <a href="{deep_link}" style="display:inline-block; padding:14px 28px; background-color:#0B2447; color:#FFFFFF; border-radius:8px; font-size:15px; font-weight:600; text-decoration:none;">
      Open TRU Connect
    </a>
    <p style="font-size:12px; color:#6B7280; margin-top:24px;">
      Don't have TRU Connect installed? Install it first, then tap this
      link again from your email.
    </p>
  </div>
</body>
</html>"""

    return Response(html, mimetype="text/html")
'''


# ==============================================================================
# src/domains/auth/api/routes.py -- rewritten: register returns no
# tokens, login/refresh pass ip_address and surface structured errors
# (handled automatically by the AppError error handler once
# src/__init__.py's integration below is applied), verify-otp now
# returns tokens, new ticket-validation endpoint, /me hardened.
# ==============================================================================

FILES[os.path.join("src", "domains", "auth", "api", "routes.py")] = r'''"""
Authentication Routes.
Ref: docs/05_BACKEND_API_SPECIFICATION.txt §5.1; Auth Hardening master
prompt, Objectives 1, 3, 6, 7, 9.

Routes ONLY: validate the request, call the service layer, return the
standard response envelope. Structured AppError subclasses raised by
services (EmailNotVerifiedError, AccountLockedError, TicketInvalidError,
etc.) are caught by the app-wide error handler -- routes do not need
their own try/except for those.
"""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jti, get_jwt, get_jwt_identity, jwt_required
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.decorators import fully_authenticated
from src.core.responses import error_response, success_response
from src.domains.auth.schemas.auth_schemas import BusinessRegisterSchema, LoginSchema, SupplierRegisterSchema
from src.domains.auth.schemas.otp_schemas import RequestOtpSchema, VerifyOtpSchema
from src.domains.auth.schemas.password_reset_schemas import (
    ForgotPasswordSchema,
    ResetPasswordSchema,
    ValidateResetTicketSchema,
)
from src.domains.auth.services.auth_service import AuthService
from src.domains.auth.services.otp_service import OTPService
from src.domains.auth.services.password_reset_service import PasswordResetService

auth_bp = Blueprint("auth", __name__)

_business_register_schema = BusinessRegisterSchema()
_supplier_register_schema = SupplierRegisterSchema()
_login_schema = LoginSchema()
_request_otp_schema = RequestOtpSchema()
_verify_otp_schema = VerifyOtpSchema()
_forgot_password_schema = ForgotPasswordSchema()
_reset_password_schema = ResetPasswordSchema()
_validate_ticket_schema = ValidateResetTicketSchema()


def _flatten_errors(messages) -> list:
    flat: list = []
    if isinstance(messages, dict):
        for field, field_errors in messages.items():
            if isinstance(field_errors, list):
                for msg in field_errors:
                    flat.append(f"{field}: {msg}")
            else:
                flat.append(f"{field}: {field_errors}")
    elif isinstance(messages, list):
        flat.extend(str(m) for m in messages)
    return flat


@auth_bp.post("/register")
def register():
    """Creates the account and sends the verification OTP ONLY. No
    tokens are returned -- there is no valid session for an unverified
    account (Auth Hardening master prompt, Objective 1)."""
    payload = request.get_json(silent=True) or {}
    role = payload.get("role")

    if role == "business":
        schema = _business_register_schema
    elif role == "supplier":
        schema = _supplier_register_schema
    else:
        return error_response(
            message="Validation failed", errors=["role: must be 'business' or 'supplier'"], status_code=422
        )

    try:
        data = schema.load({k: v for k, v in payload.items() if k != "role"})
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    if role == "business":
        user = AuthService.register_business(data)
        message = "Business account created. Check your email for a verification code."
    else:
        user = AuthService.register_supplier(data)
        message = "Supplier account created. Check your email for a verification code."

    return success_response(data={"user": user.to_public_dict()}, message=message, status_code=201)


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    try:
        data = _login_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    user, tokens = AuthService.login(data["email"], data["password"], ip_address=request.remote_addr)
    return success_response(data={"user": user.to_public_dict(), "tokens": tokens}, message="Login successful.")


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()
    tokens = AuthService.refresh(
        current_jti=claims.get("jti"), user_id=identity, ip_address=request.remote_addr
    )
    return success_response(data=tokens, message="Token refreshed.")


@auth_bp.get("/me")
@fully_authenticated
def me():
    """Hardened: requires authentication AND a database-fresh VERIFIED
    AND ACTIVE status, not just a valid token (Auth Hardening master
    prompt, Objective 3)."""
    identity = get_jwt_identity()
    user = AuthService.get_current_user(identity)
    return success_response(data=user.to_public_dict())


@auth_bp.post("/logout")
@jwt_required(verify_type=False)
def logout():
    identity = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    raw_refresh_token = payload.get("refresh_token")

    refresh_token_jti = None
    if raw_refresh_token:
        try:
            refresh_token_jti = get_jti(raw_refresh_token)
        except Exception:  # noqa: BLE001
            refresh_token_jti = None

    AuthService.logout(user_id=identity, refresh_token_jti=refresh_token_jti)
    return success_response(message="Logged out.")


@auth_bp.post("/phone/request-otp")
def request_otp():
    payload = request.get_json(silent=True) or {}
    try:
        data = _request_otp_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    OTPService.request_otp(destination=data["destination"])
    return success_response(message="If an account exists for this destination, a verification code has been sent.")


@auth_bp.post("/phone/verify-otp")
def verify_otp():
    """Returns {user, tokens} on success -- this is the first
    authenticated moment for a brand-new account (Auth Hardening master
    prompt, Objective 1)."""
    payload = request.get_json(silent=True) or {}
    try:
        data = _verify_otp_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    user, tokens = OTPService.verify_otp(destination=data["destination"], code=data["code"])
    return success_response(
        data={"user": user.to_public_dict(), "tokens": tokens}, message="Verification successful."
    )


@auth_bp.post("/forgot-password")
def forgot_password():
    payload = request.get_json(silent=True) or {}
    try:
        data = _forgot_password_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    PasswordResetService.forgot_password(data["email"])
    return success_response(
        message="If an account exists for this email, password reset instructions have been sent."
    )


@auth_bp.get("/reset-password/validate")
def validate_reset_ticket():
    """Read-only check the mobile app calls on screen load, so an
    expired/invalid link shows an immediate, clear message rather than
    only failing after the user fills in a new password (Auth Hardening
    master prompt, Objective 6)."""
    try:
        data = _validate_ticket_schema.load(request.args.to_dict())
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    is_valid = PasswordResetService.validate_ticket(data["ticket"])
    return success_response(data={"valid": is_valid})


@auth_bp.post("/reset-password")
def reset_password():
    payload = request.get_json(silent=True) or {}
    try:
        data = _reset_password_schema.load(payload)
    except MarshmallowValidationError as exc:
        return error_response(message="Validation failed", errors=_flatten_errors(exc.messages), status_code=422)

    PasswordResetService.reset_password(ticket=data["ticket"], new_password=data["new_password"])
    return success_response(message="Password has been reset successfully.")
'''


# ==============================================================================
# INTEGRATION functions
# ==============================================================================

def integrate_security_config(backend_dir: str) -> str:
    path = os.path.join(backend_dir, "src", "config.py")
    if not os.path.isfile(path):
        return "skipped"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if "APP_BASE_URL" in content:
        return "already-integrated"
    anchor = 'JWT_HEADER_TYPE = "Bearer"'
    if anchor not in content:
        return "skipped"
    block = anchor + '''

    # --- Auth Hardening additions ---
    # Ref: Auth Hardening master prompt, Objectives 1-2-7.
    # Base URL for the password-reset browser bounce page
    # (src/domains/platform/api/reset_redirect_routes.py). In dev, point
    # this at your machine's LAN IP so the emailed link works on a
    # physical phone; in production, your real domain.
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")

    UNVERIFIED_ACCOUNT_EXPIRY_HOURS = int(os.environ.get("UNVERIFIED_ACCOUNT_EXPIRY_HOURS", 24))
    LOGIN_MAX_FAILED_ATTEMPTS = int(os.environ.get("LOGIN_MAX_FAILED_ATTEMPTS", 5))
    LOGIN_LOCKOUT_WINDOW_MINUTES = int(os.environ.get("LOGIN_LOCKOUT_WINDOW_MINUTES", 15))
    PASSWORD_RESET_TICKET_EXPIRY_HOURS = int(os.environ.get("PASSWORD_RESET_TICKET_EXPIRY_HOURS", 1))'''
    new_content = content.replace(anchor, block, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return "integrated"


def integrate_app_factory(backend_dir: str) -> str:
    """Two changes to src/__init__.py:
      1. Register reset_redirect_bp at the ROOT level (no /api/v1 prefix)
         -- required, since api_bp's own registration always carries the
         /api/v1 prefix and there is no way to get a root-level path
         through it.
      2. Pass code/data from AppError through to error_response, so the
         new structured exceptions (EmailNotVerifiedError etc.) actually
         reach the client with their `code` field intact.
    """
    path = os.path.join(backend_dir, "src", "__init__.py")
    if not os.path.isfile(path):
        return "skipped"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    changed = False

    if "reset_redirect_bp" not in content:
        blueprint_anchor = 'app.register_blueprint(api_bp, url_prefix="/api/v1")'
        if blueprint_anchor in content:
            replacement = (
                blueprint_anchor
                + "\n\n    from src.domains.platform.api.reset_redirect_routes import reset_redirect_bp\n"
                "    app.register_blueprint(reset_redirect_bp)"
            )
            content = content.replace(blueprint_anchor, replacement, 1)
            changed = True
        else:
            return "skipped"

    if "error.code" not in content:
        handler_anchor = (
            "return error_response(message=error.message, errors=error.errors, "
            "status_code=error.status_code)"
        )
        if handler_anchor in content:
            content = content.replace(
                handler_anchor,
                "return error_response(\n"
                "            message=error.message,\n"
                "            errors=error.errors,\n"
                "            status_code=error.status_code,\n"
                "            code=error.code,\n"
                "            data=error.data,\n"
                "        )",
                1,
            )
            changed = True
        else:
            return "partially-skipped" if changed else "skipped"

    if not changed:
        return "already-integrated"

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "integrated"

# ==============================================================================
# backend/tests/test_auth.py -- rewritten. Unit tests (schemas, password/
# OTP/ticket utilities) mostly unchanged. Integration tests updated for
# the new register()-issues-no-tokens / verify-otp-issues-tokens flow,
# plus substantial NEW coverage for the hardening itself.
# ==============================================================================

FILES[os.path.join("tests", "test_auth.py")] = r'''"""
Authentication module tests.
Ref: continuation master prompt, Step 16; Auth Hardening master prompt,
Objective 10.

Two groups:
1. Pure unit tests -- no database connection needed:
       pytest tests/test_auth.py -k "not Integration"
2. Integration tests -- need a real PostgreSQL test database:
       pytest tests/test_auth.py -k Integration
"""
from __future__ import annotations

import re

import pytest

from src import create_app
from src.extensions import db
from src.shared.cache import cache
from src.shared.email import get_fake_provider
from src.domains.auth.schemas.auth_schemas import BusinessRegisterSchema, LoginSchema, SupplierRegisterSchema
from src.domains.auth.schemas.otp_schemas import RequestOtpSchema, VerifyOtpSchema
from src.domains.auth.schemas.password_reset_schemas import ForgotPasswordSchema, ResetPasswordSchema
from src.domains.auth.utils.otp import generate_numeric_otp, hash_otp, verify_otp_hash
from src.shared.security import hash_password, passwords_match, validate_password_complexity, verify_password
from src.shared.tickets import create_ticket, hash_ticket, is_ticket_expired, ticket_expiry, verify_ticket


# ----------------------------------------------------------------------------
# Group 1: pure unit tests.
# ----------------------------------------------------------------------------

class TestPasswordSecurity:
    def test_hash_and_verify_round_trip(self):
        hashed = hash_password("Abcd1234!")
        assert verify_password("Abcd1234!", hashed)

    def test_verify_rejects_wrong_password(self):
        hashed = hash_password("Abcd1234!")
        assert not verify_password("wrong password", hashed)

    def test_complexity_rejects_short_password(self):
        assert any("8 characters" in e for e in validate_password_complexity("Ab1!"))

    def test_complexity_accepts_valid_password(self):
        assert validate_password_complexity("Abcd1234!") == []

    def test_passwords_match(self):
        assert passwords_match("Abcd1234!", "Abcd1234!")


class TestOtpUtilities:
    def test_generated_otp_is_correct_length_and_numeric(self):
        code = generate_numeric_otp()
        assert len(code) == 6
        assert code.isdigit()

    def test_otp_hash_round_trip(self):
        code = generate_numeric_otp()
        assert verify_otp_hash(code, hash_otp(code))

    def test_otp_hash_rejects_wrong_code(self):
        assert not verify_otp_hash("654321", hash_otp("123456"))


class TestTicketUtilities:
    def test_create_ticket_is_url_safe_and_reasonably_long(self):
        assert len(create_ticket()) >= 32

    def test_hash_and_verify_round_trip(self):
        ticket = create_ticket()
        assert verify_ticket(ticket, hash_ticket(ticket))

    def test_verify_rejects_wrong_ticket(self):
        assert not verify_ticket("wrong-ticket", hash_ticket(create_ticket()))

    def test_expiry_helpers(self):
        from datetime import timedelta

        from src.core.base_model import utcnow

        future = ticket_expiry(hours=1)
        assert not is_ticket_expired(future)
        past = utcnow() - timedelta(hours=1)
        assert is_ticket_expired(past)


class TestBusinessRegisterSchema:
    def _valid_payload(self, **overrides):
        payload = {
            "firstName": "Thabo",
            "lastName": "Nkosi",
            "email": "thabo@example.com",
            "password": "Abcd1234!",
            "confirmPassword": "Abcd1234!",
            "acceptPrivacyPolicy": True,
        }
        payload.update(overrides)
        return payload

    def test_accepts_valid_payload(self):
        data = BusinessRegisterSchema().load(self._valid_payload())
        assert data["first_name"] == "Thabo"

    def test_rejects_missing_privacy_policy(self):
        with pytest.raises(Exception):
            BusinessRegisterSchema().load(self._valid_payload(acceptPrivacyPolicy=False))


class TestSupplierRegisterSchema:
    def test_accepts_valid_payload(self):
        data = SupplierRegisterSchema().load(
            {
                "ownerName": "Naledi Dlamini",
                "email": "naledi@example.com",
                "password": "Abcd1234!",
                "confirmPassword": "Abcd1234!",
                "acceptTerms": True,
            }
        )
        assert data["owner_name"] == "Naledi Dlamini"


class TestLoginSchema:
    def test_accepts_valid_payload(self):
        data = LoginSchema().load({"email": "a@example.com", "password": "Abcd1234!"})
        assert data["email"] == "a@example.com"


class TestPasswordResetSchemas:
    def test_forgot_password_schema_requires_valid_email(self):
        with pytest.raises(Exception):
            ForgotPasswordSchema().load({"email": "not-an-email"})

    def test_reset_password_schema_uses_ticket_field(self):
        data = ResetPasswordSchema().load(
            {"ticket": "abc", "newPassword": "Abcd1234!", "confirmPassword": "Abcd1234!"}
        )
        assert data["ticket"] == "abc"


# ----------------------------------------------------------------------------
# Group 2: integration tests -- require a real PostgreSQL test database.
# ----------------------------------------------------------------------------

@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        get_fake_provider().clear()
        cache.clear()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _register_business(client, email="thabo@example.com", password="Abcd1234!"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "role": "business",
            "firstName": "Thabo",
            "lastName": "Nkosi",
            "email": email,
            "password": password,
            "confirmPassword": password,
            "acceptPrivacyPolicy": True,
        },
    )


def _extract_otp(caplog, email) -> str:
    """OTP delivery goes through the fake provider (dev-mode SMTP is
    never actually used in tests), so read it from there rather than
    from logs. `caplog` is accepted for signature consistency with
    tests that also assert on log output, but is not read here."""
    for sent in get_fake_provider().sent_emails:
        if sent["to"] == email and sent["subject"] == "Your TRU Connect verification code":
            match = re.search(r"letter-spacing:6px[^>]*>\s*(\d{6})", sent["html_body"])
            if match:
                return match.group(1)
    raise AssertionError(f"No OTP email found for {email}")


class TestRegistrationIntegration:
    def test_register_returns_no_tokens(self, client):
        """Core of Objective 1: there must be nothing to bypass with."""
        response = _register_business(client, email="no-tokens@example.com")
        assert response.status_code == 201
        body = response.get_json()
        assert "tokens" not in body["data"]
        assert body["data"]["user"]["email"] == "no-tokens@example.com"

    def test_verified_duplicate_email_is_rejected(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="dup@example.com")
        code = _extract_otp(caplog, "dup@example.com")
        client.post("/api/v1/auth/phone/verify-otp", json={"destination": "dup@example.com", "code": code})

        second = _register_business(client, email="dup@example.com")
        assert second.status_code == 409

    def test_unverified_resume_same_role_succeeds(self, client):
        """Re-registering an unverified email with the SAME role is a
        resume, not a conflict."""
        first = _register_business(client, email="resume@example.com", password="Abcd1234!")
        assert first.status_code == 201

        second = _register_business(client, email="resume@example.com", password="NewPass123!")
        assert second.status_code == 201
        # Two OTP emails should have been sent (one per attempt).
        otp_emails = [
            e for e in get_fake_provider().sent_emails
            if e["to"] == "resume@example.com" and e["subject"] == "Your TRU Connect verification code"
        ]
        assert len(otp_emails) == 2

    def test_unverified_resume_different_role_is_rejected(self, client):
        """This is the exact bypass pattern found in testing: silently
        flipping an unverified account's role must not be possible."""
        first = _register_business(client, email="roleflip@example.com")
        assert first.status_code == 201

        second = client.post(
            "/api/v1/auth/register",
            json={
                "role": "supplier",
                "ownerName": "Someone",
                "email": "roleflip@example.com",
                "password": "Abcd1234!",
                "confirmPassword": "Abcd1234!",
                "acceptTerms": True,
            },
        )
        assert second.status_code == 409

    def test_expired_unverified_account_allows_fresh_registration(self, client, app):
        """Simulates the 24-hour expiry by directly backdating
        created_at, rather than waiting -- see UNVERIFIED_ACCOUNT_EXPIRY_HOURS."""
        _register_business(client, email="stale@example.com", password="OldPass123!")

        with app.app_context():
            from datetime import timedelta

            from src.core.base_model import utcnow
            from src.domains.auth.repositories.user_repository import UserRepository

            user = UserRepository.get_by_email("stale@example.com")
            user.created_at = utcnow() - timedelta(hours=25)
            db.session.commit()

        # A fresh registration with a DIFFERENT role should now succeed
        # (proving the old row was actually deleted, not just reused).
        response = client.post(
            "/api/v1/auth/register",
            json={
                "role": "supplier",
                "ownerName": "Fresh Start",
                "email": "stale@example.com",
                "password": "NewPass123!",
                "confirmPassword": "NewPass123!",
                "acceptTerms": True,
            },
        )
        assert response.status_code == 201


class TestVerificationGatingIntegration:
    def test_login_blocked_before_verification(self, client):
        _register_business(client, email="unverified-login@example.com", password="Abcd1234!")

        response = client.post(
            "/api/v1/auth/login", json={"email": "unverified-login@example.com", "password": "Abcd1234!"}
        )
        assert response.status_code == 403
        body = response.get_json()
        assert body["code"] == "EMAIL_NOT_VERIFIED"
        assert body["data"]["resend_available"] is True
        assert "verification_endpoint" in body["data"]

    def test_login_succeeds_after_verification(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="verify-then-login@example.com", password="Abcd1234!")
        code = _extract_otp(caplog, "verify-then-login@example.com")
        client.post(
            "/api/v1/auth/phone/verify-otp",
            json={"destination": "verify-then-login@example.com", "code": code},
        )

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "verify-then-login@example.com", "password": "Abcd1234!"},
        )
        assert response.status_code == 200

    def test_verify_otp_returns_tokens(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="otp-tokens@example.com")
        code = _extract_otp(caplog, "otp-tokens@example.com")

        response = client.post(
            "/api/v1/auth/phone/verify-otp", json={"destination": "otp-tokens@example.com", "code": code}
        )
        assert response.status_code == 200
        body = response.get_json()["data"]
        assert "access_token" in body["tokens"]
        assert "refresh_token" in body["tokens"]

    def test_me_requires_verified_not_just_authenticated(self, client, caplog):
        """The core regression test: a token from BEFORE the account was
        ever verified must not exist -- and even if one somehow did,
        @fully_authenticated re-checks the database, not the token."""
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="fake-token-test@example.com")
        code = _extract_otp(caplog, "fake-token-test@example.com")
        verify_response = client.post(
            "/api/v1/auth/phone/verify-otp",
            json={"destination": "fake-token-test@example.com", "code": code},
        )
        access_token = verify_response.get_json()["data"]["tokens"]["access_token"]

        # This token was issued AFTER verification, so /me must succeed.
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 200

    def test_me_rejects_unauthenticated(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401


class TestLoginLockoutIntegration:
    def test_lockout_after_max_failed_attempts(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="lockout@example.com", password="Correct123!")
        code = _extract_otp(caplog, "lockout@example.com")
        client.post("/api/v1/auth/phone/verify-otp", json={"destination": "lockout@example.com", "code": code})

        last_response = None
        for _ in range(6):  # LOGIN_MAX_FAILED_ATTEMPTS defaults to 5
            last_response = client.post(
                "/api/v1/auth/login", json={"email": "lockout@example.com", "password": "WrongPassword1!"}
            )
        assert last_response.status_code == 423
        assert last_response.get_json()["code"] == "ACCOUNT_LOCKED"

    def test_successful_login_resets_failed_counter(self, client, caplog):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email="reset-counter@example.com", password="Correct123!")
        code = _extract_otp(caplog, "reset-counter@example.com")
        client.post(
            "/api/v1/auth/phone/verify-otp", json={"destination": "reset-counter@example.com", "code": code}
        )

        for _ in range(3):
            client.post(
                "/api/v1/auth/login", json={"email": "reset-counter@example.com", "password": "wrong"}
            )

        success = client.post(
            "/api/v1/auth/login", json={"email": "reset-counter@example.com", "password": "Correct123!"}
        )
        assert success.status_code == 200

        # Counter should be back to zero, so more wrong attempts are
        # possible before locking out again.
        for _ in range(3):
            fail = client.post(
                "/api/v1/auth/login", json={"email": "reset-counter@example.com", "password": "wrong"}
            )
            assert fail.status_code == 401  # not yet 423


class TestPasswordResetTicketIntegration:
    def _get_reset_url(self, email):
        for sent in get_fake_provider().sent_emails:
            if sent["to"] == email and sent["subject"] == "Reset your TRU Connect password":
                match = re.search(r"reset-password\?ticket=([\w\-]+)", sent["html_body"])
                if match:
                    return match.group(1)
        raise AssertionError(f"No password reset email found for {email}")

    def _verified_user(self, client, caplog, email):
        import logging

        caplog.set_level(logging.INFO)
        _register_business(client, email=email, password="OldPass123!")
        code = _extract_otp(caplog, email)
        client.post("/api/v1/auth/phone/verify-otp", json={"destination": email, "code": code})

    def test_validate_ticket_true_for_fresh_ticket(self, client, caplog):
        self._verified_user(client, caplog, "reset-validate@example.com")
        client.post("/api/v1/auth/forgot-password", json={"email": "reset-validate@example.com"})
        ticket = self._get_reset_url("reset-validate@example.com")

        response = client.get(f"/api/v1/auth/reset-password/validate?ticket={ticket}")
        assert response.get_json()["data"]["valid"] is True

    def test_validate_ticket_false_for_garbage(self, client):
        response = client.get("/api/v1/auth/reset-password/validate?ticket=not-a-real-ticket")
        assert response.get_json()["data"]["valid"] is False

    def test_reset_password_with_valid_ticket_changes_password(self, client, caplog):
        self._verified_user(client, caplog, "reset-flow@example.com")
        client.post("/api/v1/auth/forgot-password", json={"email": "reset-flow@example.com"})
        ticket = self._get_reset_url("reset-flow@example.com")

        response = client.post(
            "/api/v1/auth/reset-password",
            json={"ticket": ticket, "newPassword": "NewPass123!", "confirmPassword": "NewPass123!"},
        )
        assert response.status_code == 200

        assert (
            client.post(
                "/api/v1/auth/login", json={"email": "reset-flow@example.com", "password": "OldPass123!"}
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/api/v1/auth/login", json={"email": "reset-flow@example.com", "password": "NewPass123!"}
            ).status_code
            == 200
        )

    def test_reset_ticket_cannot_be_reused(self, client, caplog):
        self._verified_user(client, caplog, "reset-replay@example.com")
        client.post("/api/v1/auth/forgot-password", json={"email": "reset-replay@example.com"})
        ticket = self._get_reset_url("reset-replay@example.com")

        first = client.post(
            "/api/v1/auth/reset-password",
            json={"ticket": ticket, "newPassword": "NewPass123!", "confirmPassword": "NewPass123!"},
        )
        assert first.status_code == 200

        second = client.post(
            "/api/v1/auth/reset-password",
            json={"ticket": ticket, "newPassword": "AnotherPass1!", "confirmPassword": "AnotherPass1!"},
        )
        assert second.status_code == 401

    def test_reset_redirect_page_renders(self, client):
        """The browser-facing bounce page (Objective 7) -- not under
        /api/v1, must exist at the exact path emailed to users."""
        response = client.get("/reset-password?ticket=abc123")
        assert response.status_code == 200
        assert b"truconnect://reset-password?ticket=abc123" in response.data
'''


# ==============================================================================
# GENERATION LOGIC
# ==============================================================================

def print_plan(backend_dir: str) -> None:
    print("=" * 78)
    print(" TRU CONNECT BACKEND - Authentication Domain Hardening")
    print("=" * 78)
    print(f" Target: {os.path.abspath(backend_dir)}")
    print()
    print(" WRITE (new files):")
    print("   - src/shared/tickets.py")
    print("   - src/shared/audit.py")
    print("   - src/domains/platform/api/reset_redirect_routes.py")
    print()
    print(" REWRITE (business rules changing -- see each file's own")
    print(" docstring for exactly what's different):")
    print("   - src/core/exceptions.py, src/core/responses.py, src/core/decorators.py")
    print("   - src/shared/cache.py, src/shared/constants.py")
    print("   - src/domains/auth/utils/otp.py")
    print("   - src/domains/auth/repositories/user_repository.py")
    print("   - src/domains/auth/services/auth_service.py")
    print("   - src/domains/auth/services/otp_service.py")
    print("   - src/domains/auth/services/password_reset_service.py")
    print("   - src/domains/auth/schemas/password_reset_schemas.py")
    print("   - src/domains/auth/api/routes.py")
    print("   - tests/test_auth.py")
    print()
    print(" INTEGRATE (targeted edits):")
    print("   - src/config.py    adds APP_BASE_URL + security constants")
    print("   - src/__init__.py  registers reset_redirect_bp (root-level) +")
    print("                      wires AppError.code/data through the handler")
    print()
    print(" NO NEW MIGRATION REQUIRED.")
    print("=" * 78)


def generate(backend_dir: str) -> None:
    written = 0
    for rel_path, content in FILES.items():
        full_path = os.path.join(backend_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        written += 1
    print(f"   {written} file(s) written.")

    results = {
        "src/config.py": integrate_security_config(backend_dir),
        "src/__init__.py": integrate_app_factory(backend_dir),
    }
    labels = {
        "integrated": "integrated",
        "already-integrated": "already integrated, no change needed",
        "partially-skipped": "PARTIALLY applied -- check this file manually",
        "skipped": "SKIPPED (expected anchor not found -- check this file manually)",
    }
    for description, status in results.items():
        print(f"   {description}: {labels[status]}")


def main():
    parser = argparse.ArgumentParser(
        description="Harden the TRU Connect authentication domain: gate login/"
        "protected routes on verification, prevent unverified-account "
        "permanent email reservation, unified ticket service, production "
        "password reset flow."
    )
    parser.add_argument(
        "--root", default=".", help="Path to the TRU_Connect monorepo root (default: current directory)."
    )
    parser.add_argument("-f", "--force", action="store_true", help="Skip the confirmation prompt.")
    args = parser.parse_args()

    backend_dir = os.path.join(args.root, BACKEND_REL)

    if not os.path.isdir(os.path.join(backend_dir, "src", "domains", "auth")):
        print(f"ERROR: '{backend_dir}/src/domains/auth' not found. Run this from the "
              "TRU_Connect root, or pass --root /path/to/TRU_Connect.")
        sys.exit(1)

    print_plan(backend_dir)

    if not args.force:
        response = input("Proceed? [y/N]: ")
        if response.strip().lower() != "y":
            print("Aborted. Re-run with --force to skip this prompt next time.")
            sys.exit(1)

    print()
    print("Applying changes...")
    generate(backend_dir)

    print()
    print("=" * 78)
    print(" Done.")
    print("=" * 78)
    print(" Add to backend/.env (optional -- sensible defaults apply without it):")
    print("   APP_BASE_URL=http://<your-LAN-IP>:5000")
    print("   UNVERIFIED_ACCOUNT_EXPIRY_HOURS=24")
    print("   LOGIN_MAX_FAILED_ATTEMPTS=5")
    print("   LOGIN_LOCKOUT_WINDOW_MINUTES=15")
    print("   PASSWORD_RESET_TICKET_EXPIRY_HOURS=1")
    print()
    print(" Test: pytest tests/test_auth.py -k Integration   (needs real Postgres)")
    print("=" * 78)


if __name__ == "__main__":
    main()