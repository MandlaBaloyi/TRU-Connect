"""
Writing terminal actions to the audit trail.

ONE HELPER, because `admin create` and the authorisation prompt both
need it and the publish block is six lines of ceremony that should not
be copied. Domain services keep their own `_record` (see
verification_service) -- this is only for the CLI's own acts, which
belong to no domain.

NEVER RAISES, and that rule is not negotiable here. The action has
already happened by the time this is called: an admin has been
created, a password has been checked. An unreachable audit backend
must not turn a completed act into a command that reports failure, or
worse, into a half-done one.

ACTOR TYPE IS ADMIN, NOT USER. The audit table distinguishes them, and
"a staff member did this at a terminal" is a materially different
sentence from "a user did this in the app" when somebody is reading
back through an incident.
"""
from __future__ import annotations

from typing import Optional


def record(
    event,
    *,
    success: bool = True,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    failure_reason: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    try:
        from src.shared.audit.audit import publish
        from src.shared.audit.audit_types import (
            ActorType,
            AuditDomain,
            AuditEvent,
            AuditStatus,
        )

        publish(
            AuditEvent(
                event_name=event,
                domain=AuditDomain.SECURITY,
                status=AuditStatus.SUCCESS if success else AuditStatus.FAILURE,
                module="cli",
                actor_type=ActorType.ADMIN,
                user_id=user_id,
                email=email,
                failure_reason=failure_reason,
                metadata={"source": "CLI", **(metadata or {})},
            )
        )
    except Exception:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).exception("cli: failed to write an audit event")
