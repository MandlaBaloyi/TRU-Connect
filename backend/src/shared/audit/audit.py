"""
Security / audit event logging + publishing.

Distinct from src/shared/monitoring.py, which is specifically the email
DELIVERY lifecycle (queued/sent/failed/retry). This module is general
authentication and security event logging: logins, lockouts,
verification-gate hits, password resets, account expiry cleanup.

TEXT LOGS: never log a password, OTP code, reset ticket, or JWT -- only
identifiers (MASKED email, user id) and IP address, matching the same
"never log sensitive values" rule the email infrastructure already
follows. This behaviour is unchanged.

WHAT'S NEW: alongside the text log, each function now PUBLISHES a
structured AuditEvent to any registered listener (in practice, Security's
audit service, which persists it to the security.audit_events table).

Two deliberate properties:

  1. EXISTING CALL SITES ARE UNCHANGED. Every function below keeps its
     original name and signature. auth_service.py, otp_service.py and
     password_reset_service.py needed zero edits for persistence to start
     working. New event types are added as new functions in the same
     style, or by calling publish() directly.

  2. MASKED IN LOGS, FULL IN THE DATABASE. mask_email() still applies to
     the text log line. The published event carries the REAL email,
     because the primary admin use case is "a user reports a problem,
     search their timeline by email" — and a masked address is
     unsearchable. Restricting who can *see* that value is an API-layer
     RBAC concern (see security/schemas/audit_schemas.py field groups),
     not a reason to destroy it at write time.

This module knows nothing about databases or the Security domain. It
builds events and hands them to listeners. Security subscribes to it;
it never reaches toward Security.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from src.shared.audit import audit_context
from src.shared.audit.audit_types import (
    ActorType,
    AuditDomain,
    AuditEvent,
    AuditEventNameType,
    AuditStatus,
)
from src.shared.audit.event_types.auth import AuthAuditEvent
from src.shared.helpers.helpers import mask_email

logger = logging.getLogger("tru_connect.audit")

_listeners: list[Callable[[AuditEvent], None]] = []


def register_listener(callback: Callable[[AuditEvent], None]) -> None:
    """
    Subscribe to published audit events. Called once at startup by
    Security's audit service. Kept as a registry (rather than a direct
    import of Security) so this module — and therefore Auth — has no
    dependency on the Security domain.
    """
    _listeners.append(callback)


def clear_listeners() -> None:
    """Test helper — lets a test isolate itself from real persistence."""
    _listeners.clear()


def publish(event: AuditEvent) -> None:
    """
    Enrich an event with request context and hand it to every listener.

    NEVER RAISES. An audit failure must not break the action being
    audited: a login that succeeded must not turn into a 500 because the
    audit table was unreachable. Failures are logged and swallowed, the
    same rule already applied to email delivery. The tradeoff is accepted
    deliberately — a lost audit row is bad, a broken login is worse, and
    the text log above still captured the event either way.
    """
    _enrich_from_request(event)
    for listener in _listeners:
        try:
            listener(event)
        except Exception:  # noqa: BLE001 — see docstring: auditing must never break the audited action
            logger.exception("audit listener failed for event=%s", event.event_name.value)


def _enrich_from_request(event: AuditEvent) -> None:
    """
    Fill request-scoped fields the caller didn't supply. Only fills what is
    still None, so an explicitly-passed value (e.g. the ip_address argument
    the existing login functions already accept) always wins.

    Safe with no request context — every getter returns None instead of
    raising, which is what lets the scheduled cleanup job publish events
    from a background thread.
    """
    if event.ip_address is None:
        event.ip_address = audit_context.get_ip_address()
    if event.user_agent is None:
        event.user_agent = audit_context.get_user_agent()
    if event.correlation_id is None:
        event.correlation_id = audit_context.get_correlation_id()
    if event.request_id is None:
        event.request_id = audit_context.get_request_id()
    if event.endpoint is None:
        event.endpoint = audit_context.get_endpoint()
    if event.http_method is None:
        event.http_method = audit_context.get_http_method()
    if event.device_id is None:
        event.device_id = audit_context.get_device_id()

    if event.browser is None and event.user_agent:
        browser, os_name, platform = audit_context.parse_user_agent(event.user_agent)
        event.browser = browser
        event.operating_system = os_name
        event.platform = platform


def _emit(
    event_name: AuthAuditEvent,
    status: AuditStatus,
    *,
    module: Optional[str] = None,
    actor_type: ActorType = ActorType.USER,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
    ip_address: Optional[str] = None,
    failure_reason: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Internal shorthand — builds an auth-domain event and publishes it."""
    publish(AuditEvent(
        event_name=event_name,
        domain=AuditDomain.AUTH,
        status=status,
        module=module,
        actor_type=actor_type,
        user_id=user_id,
        email=email,
        role=role,
        ip_address=ip_address,
        failure_reason=failure_reason,
        metadata=metadata or {},
    ))


# =============================================================================
# EXISTING FUNCTIONS — signatures unchanged, call sites untouched.
# Each now writes its original log line AND publishes a structured event.
# =============================================================================

def log_login_success(user_id: str, ip_address: Optional[str]) -> None:
    logger.info("login_success user_id=%s ip=%s", user_id, ip_address or "unknown")
    _emit(
        AuthAuditEvent.LOGIN_SUCCESS, AuditStatus.SUCCESS,
        module="auth_service", user_id=user_id, ip_address=ip_address,
    )


def log_login_failed(email: str, ip_address: Optional[str]) -> None:
    logger.warning("login_failed email=%s ip=%s", mask_email(email), ip_address or "unknown")
    _emit(
        AuthAuditEvent.LOGIN_FAILED, AuditStatus.FAILURE,
        module="auth_service", email=email, ip_address=ip_address,
        failure_reason="invalid_credentials",
    )


def log_login_locked_out(email: str, ip_address: Optional[str]) -> None:
    logger.warning("login_locked_out email=%s ip=%s", mask_email(email), ip_address or "unknown")
    _emit(
        AuthAuditEvent.LOGIN_LOCKED, AuditStatus.FAILURE,
        module="auth_service", email=email, ip_address=ip_address,
        failure_reason="account_locked_too_many_attempts",
    )


def log_login_blocked_unverified(email: str, ip_address: Optional[str]) -> None:
    logger.info("login_blocked_unverified email=%s ip=%s", mask_email(email), ip_address or "unknown")
    _emit(
        AuthAuditEvent.LOGIN_UNVERIFIED, AuditStatus.FAILURE,
        module="auth_service", email=email, ip_address=ip_address,
        failure_reason="email_not_verified",
    )


def log_unverified_account_expired(email: str) -> None:
    # Published by the scheduled cleanup job — no request context exists
    # here, which is exactly why audit_context degrades to None instead of
    # raising. actor_type=SCHEDULER distinguishes this from a user-initiated
    # deletion, which is not reconstructable after the fact.
    logger.info("unverified_account_expired email=%s", mask_email(email))
    _emit(
        AuthAuditEvent.UNVERIFIED_ACCOUNT_EXPIRED, AuditStatus.SUCCESS,
        module="cleanup_unverified_emails", actor_type=ActorType.SCHEDULER, email=email,
    )


def log_registration_role_conflict(email: str, existing_role: str, attempted_role: str) -> None:
    logger.info(
        "registration_role_conflict email=%s existing_role=%s attempted_role=%s",
        mask_email(email),
        existing_role,
        attempted_role,
    )
    _emit(
        AuthAuditEvent.REGISTER_ROLE_CONFLICT, AuditStatus.FAILURE,
        module="auth_service", email=email, role=existing_role,
        failure_reason="role_conflict",
        metadata={"existing_role": existing_role, "attempted_role": attempted_role},
    )


def log_password_reset_requested(email: str) -> None:
    logger.info("password_reset_requested email=%s", mask_email(email))
    _emit(
        AuthAuditEvent.PASSWORD_RESET_REQUESTED, AuditStatus.SUCCESS,
        module="password_reset_service", email=email,
    )


def log_password_reset_completed(user_id: str) -> None:
    logger.info("password_reset_completed user_id=%s", user_id)
    _emit(
        AuthAuditEvent.PASSWORD_RESET_SUCCESS, AuditStatus.SUCCESS,
        module="password_reset_service", user_id=user_id,
    )


# =============================================================================
# NEW FUNCTIONS — call sites for these do not exist yet. Wire them into
# otp_service.py / auth_service.py as a follow-up; each is additive and
# independent, so they can be adopted one at a time.
# =============================================================================

def log_register_success(user_id: str, email: str, role: str) -> None:
    logger.info("register_success user_id=%s email=%s role=%s", user_id, mask_email(email), role)
    _emit(
        AuthAuditEvent.REGISTER_SUCCESS, AuditStatus.SUCCESS,
        module="auth_service", user_id=user_id, email=email, role=role,
    )


def log_register_failed(email: str, reason: str) -> None:
    logger.warning("register_failed email=%s reason=%s", mask_email(email), reason)
    _emit(
        AuthAuditEvent.REGISTER_FAILED, AuditStatus.FAILURE,
        module="auth_service", email=email, failure_reason=reason,
    )


def log_register_resumed(email: str, role: str) -> None:
    """
    Distinct from log_register_success: this is the "same email, same
    role, still within the unverified window, profile fields updated and
    a new OTP sent" path in auth_service._create_or_resume — the SAME
    account row, not a new one. Worth its own event because "someone
    tried to register this email again" and "a brand new account was
    created" are different stories to an investigator.
    """
    logger.info("register_resumed email=%s role=%s", mask_email(email), role)
    _emit(
        AuthAuditEvent.REGISTER_RESUMED, AuditStatus.SUCCESS,
        module="auth_service", email=email, role=role,
    )


def log_otp_created(user_id: str, email: str) -> None:
    logger.info("otp_created user_id=%s email=%s", user_id, mask_email(email))
    _emit(
        AuthAuditEvent.OTP_CREATED, AuditStatus.SUCCESS,
        module="otp_service", user_id=user_id, email=email,
    )


def log_otp_verified(user_id: str, email: str) -> None:
    logger.info("otp_verified user_id=%s email=%s", user_id, mask_email(email))
    _emit(
        AuthAuditEvent.OTP_VERIFIED, AuditStatus.SUCCESS,
        module="otp_service", user_id=user_id, email=email,
    )


def log_otp_failed(email: str, reason: str) -> None:
    logger.warning("otp_failed email=%s reason=%s", mask_email(email), reason)
    _emit(
        AuthAuditEvent.OTP_FAILED, AuditStatus.FAILURE,
        module="otp_service", email=email, failure_reason=reason,
    )


def log_otp_resent(user_id: str, email: str) -> None:
    logger.info("otp_resent user_id=%s email=%s", user_id, mask_email(email))
    _emit(
        AuthAuditEvent.OTP_RESENT, AuditStatus.SUCCESS,
        module="otp_service", user_id=user_id, email=email,
    )


def log_email_verified(user_id: str, email: str) -> None:
    logger.info("email_verified user_id=%s email=%s", user_id, mask_email(email))
    _emit(
        AuthAuditEvent.EMAIL_VERIFIED, AuditStatus.SUCCESS,
        module="otp_service", user_id=user_id, email=email,
    )


def log_token_created(user_id: str) -> None:
    logger.info("token_created user_id=%s", user_id)
    _emit(
        AuthAuditEvent.TOKEN_CREATED, AuditStatus.SUCCESS,
        module="auth_service", user_id=user_id,
    )


def log_token_refreshed(user_id: str) -> None:
    logger.info("token_refreshed user_id=%s", user_id)
    _emit(
        AuthAuditEvent.TOKEN_REFRESHED, AuditStatus.SUCCESS,
        module="auth_service", user_id=user_id,
    )


def log_token_revoked(user_id: str, reason: str = "logout") -> None:
    """
    Every revocation is meaningful regardless of cause — `reason`
    distinguishes why: "logout" (explicit sign-out), "rotation" (old
    token revoked as part of issuing a new one via refresh), or any
    future cause a caller wants to record, rather than collapsing them
    into one undifferentiated event.
    """
    logger.info("token_revoked user_id=%s reason=%s", user_id, reason)
    _emit(
        AuthAuditEvent.TOKEN_REVOKED, AuditStatus.SUCCESS,
        module="auth_service", user_id=user_id,
        metadata={"reason": reason},
    )


def log_logout(user_id: str) -> None:
    logger.info("logout user_id=%s", user_id)
    _emit(
        AuthAuditEvent.LOGOUT, AuditStatus.SUCCESS,
        module="auth_service", user_id=user_id,
    )


def log_rate_limit_exceeded(
    event_name: AuditEventNameType,
    ip_address: Optional[str],
    email: Optional[str] = None,
    user_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    http_method: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """
    ONE function for every rate-limited route, not one per route —
    unlike the LOGIN_*/REGISTER_*/etc. functions above (which each
    correspond to one specific business outcome), "a rate limit was
    exceeded" is the same kind of event everywhere it happens; only
    event_name changes per call site (rate_limit/policies.py's
    RATE_LIMIT_AUDIT_EVENTS maps each route to its own specific
    event name, e.g. LOGIN_RATE_LIMITED vs REGISTER_RATE_LIMITED).

    user_id is almost always None here BY DESIGN, not by omission: the
    rate limiter runs BEFORE authentication on every route it guards
    (see the decorator ordering in auth/api/routes.py), specifically so
    a flood of requests is rejected before any auth work happens at
    all. That means there is usually no verified identity yet at the
    moment a limit trips — ip_address and, where the route has one,
    email are what's actually available, which is why AuditEvent makes
    almost every field Optional in the first place.
    """
    logger.warning(
        "rate_limit_exceeded event=%s ip=%s endpoint=%s",
        event_name.value, ip_address or "unknown", endpoint or "unknown",
    )
    publish(AuditEvent(
        event_name=event_name,
        domain=AuditDomain.AUTH,
        status=AuditStatus.FAILURE,
        module="rate_limit",
        actor_type=ActorType.ANONYMOUS if user_id is None else ActorType.USER,
        user_id=user_id,
        email=email,
        ip_address=ip_address,
        endpoint=endpoint,
        http_method=http_method,
        failure_reason="rate_limit_exceeded",
        metadata=metadata or {},
    ))
