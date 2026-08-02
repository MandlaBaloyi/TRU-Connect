"""
Serialization for the Security Control Center — with RBAC/ABAC field
groups built in from day one.

WHY FIELD GROUPS RATHER THAN ONE SERIALIZER: an audit row contains
fields that different privileged roles should and should not see. A
Compliance Officer reviewing process adherence does not need raw IP
addresses and device fingerprints; a Platform Owner investigating an
incident does. Writing one dump-everything serializer now would mean
retrofitting redaction later across every endpoint — the expensive kind
of change.

So the visibility tiers are defined here, before any route exists. The
future API route picks a tier from the caller's role and passes it in.

The tiers are additive: FULL includes INVESTIGATOR includes BASIC.

NOTE: this module defines WHAT each tier may see. It does not decide WHO
gets which tier — that mapping is an API-layer authorization concern and
lives with the route, so that changing a role's permissions never means
editing a serializer.
"""

from __future__ import annotations

import enum
from typing import Any, Optional

from src.shared.helpers import mask_email


class FieldGroup(str, enum.Enum):
    BASIC = "basic"                # what happened, when, roughly to whom
    INVESTIGATOR = "investigator"  # + network/device/correlation detail
    FULL = "full"                  # + raw metadata, user agent, device id


# What happened — never restricted; without these a row is meaningless.
_BASIC_FIELDS = (
    "id", "timestamp", "domain", "module", "event_name",
    "category", "severity", "status", "failure_reason", "actor_type",
)

# Enough to follow an incident across requests and origins.
_INVESTIGATOR_FIELDS = (
    "user_id", "role", "tenant_id", "ip_address", "correlation_id",
    "request_id", "session_id", "http_method", "endpoint", "http_status_code",
    "browser", "operating_system", "platform",
)

# Highest-sensitivity: fingerprinting-grade and free-form payloads.
_FULL_FIELDS = ("user_agent", "device_id", "metadata")


def serialize(record, group: FieldGroup = FieldGroup.BASIC) -> dict[str, Any]:
    """
    Turn one AuditEventRecord into a dict for JSON output.

    EMAIL HANDLING: stored in full, but only REVEALED in full at
    INVESTIGATOR tier and above. BASIC callers get a masked address — they
    can still see that the same actor recurs across rows without the
    address itself being exposed. This is the "mask presentation, never
    mask storage" rule applied at the only place it belongs: output.
    """
    out: dict[str, Any] = {}

    for name in _BASIC_FIELDS:
        value = getattr(record, name, None)
        out[name] = str(value) if name == "id" and value is not None else value

    if record.timestamp is not None:
        out["timestamp"] = record.timestamp.isoformat()

    if group in (FieldGroup.INVESTIGATOR, FieldGroup.FULL):
        out["email"] = record.email
        for name in _INVESTIGATOR_FIELDS:
            value = getattr(record, name, None)
            out[name] = str(value) if value is not None and name in ("user_id", "tenant_id") else value
    else:
        out["email"] = mask_email(record.email) if record.email else None

    if group is FieldGroup.FULL:
        out["user_agent"] = record.user_agent
        out["device_id"] = record.device_id
        out["metadata"] = record.event_metadata or {}

    return out


def serialize_many(records, group: FieldGroup = FieldGroup.BASIC) -> list[dict[str, Any]]:
    return [serialize(r, group) for r in records]


def serialize_page(page_result, group: FieldGroup = FieldGroup.BASIC) -> dict[str, Any]:
    """
    Serialize a PageResult from the repository into the response envelope
    the control center's infinite-scroll / pagination controls will consume.
    """
    return {
        "items": serialize_many(page_result.items, group),
        "next_cursor": page_result.next_cursor,
        "has_more": page_result.has_more,
    }
