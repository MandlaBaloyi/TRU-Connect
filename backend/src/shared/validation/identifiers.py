"""
Identifier normalization — turns messy real-world input into the
canonical form used for INDEXED MATCHING (not display). Scope matches
this module's sibling validators.py: infrastructure-level, format/shape
only, never business rules.

WHY THIS EXISTS: nothing in this codebase normalized phone numbers
before Supplier Discovery needed it (confirmed by reading
user_repository.py — email normalization there is just an inline
`.strip().lower()`, and nothing touches phone at all). Real South
African phone input varies too much for that inline-regex approach to
be safe here — leading zero vs +27, spaces, dashes, users pasting a
number with a stray "tel:" prefix. Using `phonenumbers` (Google's
libphonenumber, the same library iOS/Android's own dialers use) is
worth the dependency rather than re-deriving that logic badly.

Shared here (not owned by connections alone) since normalizing
a phone number for matching is a cross-cutting concern other domains
will eventually want too (OTP delivery already touches phone numbers,
just doesn't normalize them for matching yet).
"""
from __future__ import annotations

from typing import Optional

import phonenumbers

# Default region for parsing a NATIONAL-format number (one without a
# leading + / country code) — TRU Connect's userbase, per every
# existing example throughout this codebase (+27...). A number that's
# already in full international format (+<any country>...) is parsed
# correctly regardless of this default.
DEFAULT_REGION = "ZA"


def normalize_email(value: str) -> str:
    """Matches the existing inline convention in user_repository.py
    exactly (`.strip().lower()`) — this function exists so
    connections doesn't re-derive that logic locally, not to
    change what it does."""
    return value.strip().lower()


def normalize_phone(value: str, region: str = DEFAULT_REGION) -> Optional[str]:
    """Returns E.164 (e.g. "+27712345678") for a valid, real number, or
    None if the input isn't parseable/valid — callers decide what a
    None means for them (e.g. "this can't be a phone search, try it as
    a name instead"), this function never guesses.

    NEVER raises on bad input — phonenumbers.NumberParseException is
    caught and turned into None, since this runs on arbitrary user
    search input that's expected to sometimes just be wrong.
    """
    try:
        parsed = phonenumbers.parse(value, region)
    except phonenumbers.NumberParseException:
        return None

    if not phonenumbers.is_valid_number(parsed):
        return None

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def looks_like_phone(value: str) -> bool:
    """Cheap pre-check so callers can decide "try phone matching"
    without paying for a full parse on obviously-not-a-phone input
    (e.g. a business name search). Deliberately permissive — the real
    validity check is normalize_phone()'s job, not this one's."""
    digits_and_symbols = value.strip()
    if not digits_and_symbols:
        return False
    stripped = digits_and_symbols.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if stripped.startswith("+"):
        stripped = stripped[1:]
    return stripped.isdigit() and 7 <= len(stripped) <= 15


def escape_like_pattern(value: str) -> str:
    """Escapes SQL LIKE/ILIKE's three special characters (%, _, and
    the escape character itself) in raw user input BEFORE it gets
    turned into a search pattern -- shared by
    SupplierProfileRepository.search_by_name_prefix and
    BusinessProfileRepository.search_by_name_prefix (Find Supplier /
    Find Business), found as a real gap while reviewing search
    behaviour: without this, someone searching for the literal
    business name "50% Off Traders" would have their own "%"
    interpreted as a wildcard, and someone searching a single "%"
    character would get back the first N results alphabetically
    instead of a real narrow match -- not a data-exposure risk (the
    caller already only returns the same narrow, already-masked
    fields any search result shows), but a genuine correctness bug in
    what "search" means.

    Callers still append their own trailing "%" for the prefix match
    AFTER calling this -- this function only escapes what the PERSON
    typed, never adds the wildcard itself.
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
