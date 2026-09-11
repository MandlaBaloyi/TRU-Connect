"""
Every privileged terminal act leaves a trail.

THE GAP THIS CLOSES. Verification decisions were audited from the day
they were written. Minting a staff account and accepting a catalogue
match were not -- which is backwards, because `flask admin create`
produces an account that can reshape the shared catalogue, and
`catalogue accept` writes a GLOBAL ALIAS affecting every supplier on
the platform. Both left no trace outside shell history, which is
per-machine, per-user, and trivially cleared.

THE MOST VALUABLE EVENT IS THE FAILED ONE. A successful staff action
leaves other traces -- a changed row, an email, an alias. A FAILED
attempt at the privileged door leaves none at all, and repeated
failures are exactly the signal somebody wants after an incident.

These tests read security.audit_events directly rather than mocking
the publisher, because "was it actually written to the table a
regulator would read" is the only version of this question worth
asserting.

THE CATALOGUE HALF LIVES IN
tests/domains/catalogue/matching/test_review_service.py, next to the
fixtures that already build a product, an offer and a pending review.
Duplicating that setup here to keep the audit tests in one file would
have meant maintaining two versions of it.
"""
from __future__ import annotations

import click
import pytest

from src.domains.auth.models.user import UserRole, VerificationStatus
from src.extensions import db

PASSWORD = "Str0ng!Passw0rd"


@pytest.fixture(autouse=True)
def no_ambient_admin_env(monkeypatch):
    from src.cli.commands.admin import ENV_ADMIN_EMAIL, ENV_ADMIN_PASSWORD

    monkeypatch.delenv(ENV_ADMIN_EMAIL, raising=False)
    monkeypatch.delenv(ENV_ADMIN_PASSWORD, raising=False)


@pytest.fixture()
def make_admin(make_user, db_session):
    def _make(email: str = "staff@truconnect.co.za", **overrides):
        user = make_user(
            email,
            role=UserRole.ADMIN,
            verification_status=VerificationStatus.VERIFIED,
            password=PASSWORD,
            **overrides,
        )
        db_session.commit()
        return user

    return _make


def _answer(monkeypatch, *responses):
    queue = list(responses)
    monkeypatch.setattr(click, "prompt", lambda *a, **k: queue.pop(0))


def _events(name: str):
    """Audit rows for one event name, newest first."""
    return db.session.execute(
        db.text(
            "SELECT user_id, email, status, failure_reason, metadata "
            "FROM security.audit_events WHERE event_name = :n "
            "ORDER BY timestamp DESC"
        ),
        {"n": name},
    ).fetchall()


class TestTheTerminalDoor:
    def test_a_successful_sign_in_is_recorded(self, app, db_session, make_admin, monkeypatch):
        from src.cli._shared.authorise import require_capability
        from src.cli._shared.capabilities import CATALOGUE_REVIEW

        admin = make_admin()
        _answer(monkeypatch, admin.email, PASSWORD)

        require_capability(CATALOGUE_REVIEW)

        rows = _events("admin.cli_sign_in_succeeded")
        assert len(rows) == 1
        assert str(rows[0][0]) == str(admin.id)
        assert rows[0][4]["capability"] == CATALOGUE_REVIEW

    def test_a_FAILED_sign_in_is_recorded(self, app, db_session, make_admin, monkeypatch):
        """THE ONE THAT MATTERS MOST. Nothing else in the system records
        that somebody tried and failed at the privileged door."""
        from src.cli._shared.authorise import require_capability
        from src.cli._shared.capabilities import CATALOGUE_REVIEW

        admin = make_admin()
        _answer(monkeypatch, admin.email, "wrong-password")

        with pytest.raises(click.ClickException):
            require_capability(CATALOGUE_REVIEW)

        rows = _events("admin.cli_sign_in_failed")
        assert len(rows) == 1
        assert rows[0][1] == admin.email
        assert rows[0][2] == "failure"
        assert rows[0][3] == "invalid_credentials"

    def test_the_right_password_on_a_non_admin_is_its_own_event(
        self, app, db_session, make_user, monkeypatch
    ):
        """"Wrong password" and "correct password, wrong account" are
        different facts. The second is the more interesting one."""
        from src.cli._shared.authorise import require_capability
        from src.cli._shared.capabilities import CATALOGUE_REVIEW

        user = make_user(
            "shop@example.com",
            role=UserRole.BUSINESS,
            verification_status=VerificationStatus.VERIFIED,
            password=PASSWORD,
        )
        db_session.commit()
        _answer(monkeypatch, user.email, PASSWORD)

        with pytest.raises(click.ClickException):
            require_capability(CATALOGUE_REVIEW)

        assert _events("admin.cli_sign_in_failed") == []
        denied = _events("admin.cli_capability_denied")
        assert len(denied) == 1
        assert denied[0][4]["role"] == "business"


class TestMintingStaff:
    def test_the_bootstrap_admin_is_recorded_as_unapproved(self, app, db_session, monkeypatch):
        """THE FIRST ADMIN IS THE ONE NOBODY AUTHORISED, by necessity.
        That is precisely why the row has to say so -- it is the single
        account in the system whose existence rests on shell access
        alone."""
        from src.cli.commands.admin import create_admin

        _answer(monkeypatch, PASSWORD)
        monkeypatch.setattr(click, "confirm", lambda *a, **k: True)

        create_admin.callback.__wrapped__(
            email="first@truconnect.co.za", first_name="First", last_name=""
        )

        rows = _events("admin.staff_account_created")
        assert len(rows) == 1
        assert rows[0][4]["bootstrap"] is True
        assert rows[0][4]["authorised_by"] is None

    def test_a_seeded_admin_is_a_distinct_event(self, app, db_session, monkeypatch):
        """"A person typed this" and "a deploy script read it from .env"
        answer the who question differently."""
        from src.cli.commands.admin import ENV_ADMIN_EMAIL, ENV_ADMIN_PASSWORD, seed_admin

        monkeypatch.setenv(ENV_ADMIN_EMAIL, "seeded@truconnect.co.za")
        monkeypatch.setenv(ENV_ADMIN_PASSWORD, PASSWORD)

        seed_admin.callback.__wrapped__()

        assert len(_events("admin.staff_account_seeded")) == 1
        assert _events("admin.staff_account_created") == []
