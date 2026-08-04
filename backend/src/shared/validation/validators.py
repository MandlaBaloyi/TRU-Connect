"""
Infrastructure-level validators.
 "Shared Notification Infrastructure" lists
validators.py explicitly. Scope is deliberately narrow: format/shape
validation useful to infrastructure code (e.g. "is this a plausible
email address before we even try to send to it"), NEVER business rules
(those belong in each domain's own schemas, e.g.
src/domains/auth/schemas/auth_schemas.py already validates registration
emails with Marshmallow's fields.Email).
"""
from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def is_plausible_email(value: str) -> bool:
    """Cheap sanity check before attempting to send -- NOT a replacement
    for proper validation at the API boundary (Marshmallow fields.Email
    already does that, using the email-validator package, before a
    request's data ever reaches a service)."""
    return bool(_EMAIL_RE.match(value))
