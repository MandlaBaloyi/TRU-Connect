"""
Serialization for the future Security Control Center -- RBAC field
groups. Relocated from security/schemas/ to security/audit/schemas/.
"""

from __future__ import annotations

import enum

from src.shared.helpers.helpers import mask_email


class FieldGroup(str, enum.Enum):
    BASIC = "basic"
    INVESTIGATOR = "investigator"
    FULL = "full"


def serialize(record, group: FieldGroup = FieldGroup.BASIC) -> dict:
    out = {"event_name": record.event_name}
    out["email"] = record.email if group != FieldGroup.BASIC else mask_email(record.email)
    return out
