"""
Small, generic infrastructure helpers.
Shared Notification Infrastructure" lists helpers.py
explicitly. Only cross-cutting, non-domain helpers belong here -- e.g.
formatting for safe logging, never business rules.
"""
from __future__ import annotations


def mask_email(email: str) -> str:
    """Masks an email address for safe logging (originally) --
    "LOGGING"/"SECURITY" -- never log sensitive values in full).
    Example: "mandla@example.com" -> "m***a@example.com".

    ALSO used by network/connections for search-result display
    (file.txt §4: enough to recognise the supplier, never the full
    identifier) -- same masking, a second legitimate use, not a scope
    creep of what this function does.
    """
    if "@" not in email:
        return "***"
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(e164_phone: str) -> str:
    """Masks an E.164 phone number for display -- keeps the country
    code and last 2 digits visible, masks the middle. Added for
    network/connections's search results (file.txt §4) --
    deliberately lives beside mask_email rather than in that domain
    locally, since "mask an identifier for safe partial display" is
    exactly this module's existing scope, not a domain-specific rule.
    Example: "+27712345678" -> "+27 71••••••78".
    """
    digits = e164_phone.replace(" ", "")
    if len(digits) < 6:
        return "***"
    country_and_start = digits[:5]  # e.g. "+2771"
    last_two = digits[-2:]
    return f"{country_and_start[:3]} {country_and_start[3:]}{'•' * 6}{last_two}"


def truncate(value: str, max_length: int = 200) -> str:
    """Defensive truncation for anything interpolated into a log message
    or error response, so a pathological input can't blow up log
    storage."""
    if len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."
