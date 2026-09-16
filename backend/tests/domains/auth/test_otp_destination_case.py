"""
Verifying an email address that was typed with a capital letter.

THE BUG THIS PINS, found by Mandla failing to verify his own account
while typing a code I had read straight out of the database and knew to
be correct:

    otp_service.verify_otp compared the stored destination against the
    submitted one RAW:

        if record.destination != destination or not verify_otp_hash(...)

    UserRepository.get_by_email normalises (.strip().lower()), so
    somebody who registered as "Thabo@example.com" WAS found -- and
    then failed that comparison against the stored, lowercased
    "thabo@example.com" BEFORE the code was ever checked.

    The account was unverifiable forever, and the message shown was
    "Incorrect verification code" -- which sends a person to re-read
    the email, request new codes, and blame the one thing that was not
    broken. Any email with a single capital letter or a stray space was
    affected, which on a phone keyboard that auto-capitalises the first
    letter is a great many of them.

THE GUARD ITSELF IS CORRECT AND STAYS. A code issued for one address
must never verify a different one -- that is the whole reason the
comparison exists, and the last test here holds it.

WHY THIS NEEDED ITS OWN FILE. Every existing OTP test registers and
verifies with the SAME lowercase literal, so the comparison could never
fail in them. The bug lived in the gap between two functions that each
looked right on their own.
"""
from __future__ import annotations

import re

import pytest

from src.shared.email.email import get_fake_provider


def _register(client, email: str):
    return client.post(
        "/api/v1/auth/register",
        json={
            "role": "business",
            "firstName": "Thabo",
            "lastName": "Nkosi",
            "businessName": "Nkosi Spaza",
            "email": email,
            "password": "Abcd1234!",
            "confirmPassword": "Abcd1234!",
            "acceptPrivacyPolicy": True,
        },
    )


def _extract_otp(email: str) -> str:
    """The fake provider records what was sent. Matched
    case-insensitively on the recipient, because the whole point here
    is that the address travels in more than one casing."""
    for sent in get_fake_provider().sent_emails:
        if sent["to"].lower() == email.lower() and sent["subject"] == "Your TruConnect verification code":
            match = re.search(r"letter-spacing:6px[^>]*>\s*(\d{6})", sent["html_body"])
            if match:
                return match.group(1)
    raise AssertionError(f"No OTP email found for {email}")


@pytest.mark.parametrize(
    "registered_as,verified_as",
    [
        pytest.param("Thabo@example.com", "Thabo@example.com", id="capital-throughout"),
        pytest.param("thabo@example.com", "Thabo@example.com", id="capital-only-at-verify"),
        pytest.param("Thabo@example.com", "thabo@example.com", id="capital-only-at-register"),
        pytest.param("THABO@EXAMPLE.COM", "thabo@example.com", id="shouting"),
        # WHITESPACE ONLY AT VERIFY, never at register: fields.Email
        # refuses a padded address up front with a 422, so that half
        # cannot arise. What CAN arise is a client padding the
        # destination it posts back -- which normalize_email also
        # covers, and which the raw comparison did not.
        pytest.param("thabo@example.com", "  thabo@example.com  ", id="padded-at-verify"),
    ],
)
def test_casing_does_not_stop_a_real_code_working(client, registered_as, verified_as):
    """THE REGRESSION. A phone keyboard capitalises the first letter of
    a field by default, so this is the ordinary case, not an edge
    one."""
    response = _register(client, registered_as)
    assert response.status_code == 201

    code = _extract_otp(registered_as)

    verify = client.post(
        "/api/v1/auth/phone/verify-otp",
        json={"destination": verified_as, "code": code},
    )

    assert verify.status_code == 200, (
        f"registered as {registered_as!r}, verified as {verified_as!r} -- "
        "casing must not decide whether a correct code is accepted"
    )


def test_a_wrong_code_is_still_refused(client):
    """The fix must not have turned the check into a no-op."""
    _register(client, "Casing.Check@example.com")

    verify = client.post(
        "/api/v1/auth/phone/verify-otp",
        json={"destination": "casing.check@example.com", "code": "000000"},
    )

    assert verify.status_code == 401


def test_a_code_issued_for_one_address_cannot_verify_another(client):
    """THE REASON THE COMPARISON EXISTS AT ALL, and the thing the fix
    had to preserve. Normalising the two sides must not let a code
    issued for one person verify somebody else."""
    _register(client, "first@example.com")
    _register(client, "second@example.com")

    first_code = _extract_otp("first@example.com")

    verify = client.post(
        "/api/v1/auth/phone/verify-otp",
        json={"destination": "second@example.com", "code": first_code},
    )

    assert verify.status_code in (401, 403), (
        "a code issued for one address must never verify a different one"
    )
