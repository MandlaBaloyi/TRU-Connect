"""
shared.validation.business_name -- the one rule shared by supplier
registration and supplier profile edit.
"""
from __future__ import annotations

import pytest

from src.shared.validation.business_name import normalize_business_name


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("MacMan Businesses", "MacMan Businesses"),
        ("  MacMan   Businesses  ", "MacMan Businesses"),  # trim + collapse
        ("AB", "AB"),  # exactly the minimum
        ("4Kids Toys", "4Kids Toys"),  # digits fine as long as a letter is present
        ("Zoë's Café", "Zoë's Café"),  # non-ASCII letters count
    ],
)
def test_accepts_and_normalizes(raw, expected):
    assert normalize_business_name(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "a",  # too short
        "x" * 51,  # too long
        "1234",  # no letter
        "----",  # no letter
        "aaaa",  # single repeated character
        "!!!",  # single repeated character, no letter
    ],
)
def test_rejects(raw):
    with pytest.raises(ValueError) as exc:
        normalize_business_name(raw)
    assert isinstance(exc.value.args[0], list)
    assert exc.value.args[0]  # at least one human-readable message
