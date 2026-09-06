"""
Business-name normalization + validation, shared by the two places a
business name is accepted from user input:

  * supplier registration  (auth/schemas/auth_schemas.py -- now a
    MANDATORY field, was previously an optional, silently-discarded one)
  * supplier profile edit  (supplier/supplier_profile/services/
    supplier_profile_service.py)

Lives here rather than in either domain because BOTH need the identical
rule and neither should import the other's schema/service. Same
cross-cutting reasoning as identifiers.py's phone normalization next
door -- this is shape/plausibility ("is this a real name someone
typed"), deliberately not a deeper business rule (no profanity list,
no uniqueness check -- those, if they ever exist, belong to the owning
domain).

THE RULE (agreed during the Community redesign round, from the
Relationship Intelligence plan):
  * 2-50 characters after trimming + collapsing internal whitespace
  * must contain at least one letter (any script) -- rejects "1234",
    "----", "   "
  * not a single repeated character -- rejects "aaaa", "!!!!" (a real
    name has at least two distinct non-space characters)
"""
from __future__ import annotations

import re

MIN_BUSINESS_NAME_LENGTH = 2
MAX_BUSINESS_NAME_LENGTH = 50

_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)
_WHITESPACE_RUN_RE = re.compile(r"\s+")


def normalize_business_name(raw: str) -> str:
    """Returns the cleaned name (trimmed, internal whitespace collapsed
    to single spaces) or raises ``ValueError`` whose ``args[0]`` is a
    list of human-readable messages -- matching how
    supplier_profile_service.py already collects field errors, and easy
    for a Marshmallow ``@validates`` hook to re-raise.
    """
    name = _WHITESPACE_RUN_RE.sub(" ", (raw or "").strip())
    errors: list[str] = []

    if len(name) < MIN_BUSINESS_NAME_LENGTH:
        errors.append(f"Business name must be at least {MIN_BUSINESS_NAME_LENGTH} characters.")
    elif len(name) > MAX_BUSINESS_NAME_LENGTH:
        errors.append(f"Business name must be {MAX_BUSINESS_NAME_LENGTH} characters or fewer.")

    if name and not _LETTER_RE.search(name):
        errors.append("Business name must contain at least one letter.")

    if len(set(name.replace(" ", ""))) == 1:
        errors.append("Enter a real business name.")

    if errors:
        raise ValueError(errors)

    return name
