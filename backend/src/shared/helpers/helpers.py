"""
Small, generic infrastructure helpers.
Shared Notification Infrastructure" lists helpers.py
explicitly. Only cross-cutting, non-domain helpers belong here -- e.g.
formatting for safe logging, never business rules.
"""
from __future__ import annotations


def mask_email(email: str) -> str:
    """Masks an email address for safe logging 
    "LOGGING"/"SECURITY" -- never log sensitive values in full).
    Example: "mandla@example.com" -> "m***a@example.com".
    """
    if "@" not in email:
        return "***"
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def truncate(value: str, max_length: int = 200) -> str:
    """Defensive truncation for anything interpolated into a log message
    or error response, so a pathological input can't blow up log
    storage."""
    if len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."
