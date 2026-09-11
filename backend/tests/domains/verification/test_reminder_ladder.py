"""
The verification emails: the two transactional ones, and the ladder.

WHAT IS ACTUALLY BEING DEFENDED HERE, beyond "an email went out":

  THAT THE INTERNAL REASON NEVER REACHES THE SUPPLIER. A revocation
  reason is written for us and may read "documents appear altered".
  One careless interpolation puts an internal assessment in the inbox
  of the person it describes, and nothing about that failure is
  visible in review -- the email still sends, still looks right, and
  is wrong only in a way the recipient notices.

  THAT THE LADDER STOPS. Three rungs, then silence. A sweep that ran
  every six hours forever against somebody's inbox would be the worst
  possible outcome of a reminder feature.

  THAT DEPLOY DAY IS NOT A MAILSTORM. Every existing unverified
  supplier has an old created_at. Without the fallback rule they would
  each receive all three emails within the first few sweeps.

Email is captured through the FAKE PROVIDER (MAIL_PROVIDER=fake in
TestingConfig), so these assert on what would actually have been sent
rather than on a mock of our own making.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from src.core.base_model import utcnow
from src.domains.supplier.supplier_profile.models.supplier_profile import (
    SupplierVerificationStatus,
)
from src.domains.verification.jobs import verification_reminder_sweep as sweep
from src.domains.verification.notification_templates import verification_emails
from src.domains.verification.services import verification_service
from src.extensions import db


@pytest.fixture()
def mailbox(app):
    """The in-memory fake provider, emptied before each test."""
    from src.shared.email.email import get_fake_provider

    provider = get_fake_provider()
    provider.clear()
    return provider


@pytest.fixture()
def make_admin_user(make_user, db_session):
    from src.domains.auth.models.user import UserRole, VerificationStatus

    def _make(email: str = "staff@truconnect.co.za"):
        user = make_user(email, role=UserRole.ADMIN, verification_status=VerificationStatus.VERIFIED)
        db_session.commit()
        return user

    return _make


@pytest.fixture()
def hidden_supplier(make_supplier, make_supplier_profile):
    """A supplier nobody can see, with the ladder untouched."""

    def _make(email: str = "hidden@example.com", business_name: str = "Hidden Wholesale"):
        user = make_supplier(email)
        profile = make_supplier_profile(
            user,
            business_name=business_name,
            verification_status=SupplierVerificationStatus.UNVERIFIED,
        )
        profile.verification_reminder_stage = 0
        profile.verification_reminder_sent_at = None
        db.session.commit()
        return user, profile

    return _make


def _age(profile, **delta):
    """Backdate the ladder's clock so a rung falls due."""
    profile.verification_reminder_sent_at = utcnow() - timedelta(**delta)
    db.session.commit()


class TestTransactionalEmails:
    def test_approval_tells_the_supplier_their_shop_is_live(
        self, app, db_session, mailbox, hidden_supplier, make_admin_user
    ):
        """Until this existed, approving changed a database row and told
        the supplier nothing -- they would have found out by chance,
        next time they opened Settings."""
        user, _ = hidden_supplier()

        verification_service.approve(
            user.id, decided_by_user_id=str(make_admin_user().id), reason="Certificate checked."
        )

        assert len(mailbox.sent_emails) == 1
        message = mailbox.sent_emails[0]
        assert message["to"] == user.email
        assert "live" in message["subject"].lower()

    def test_revocation_sends_NOTHING(
        self, app, db_session, mailbox, make_supplier, make_supplier_profile, make_admin_user
    ):
        """DELIBERATE, and previously the opposite.

        A revocation email was built and then removed. The supplier
        already sees the state in Settings the moment they look, and an
        unsolicited email about a decision whose real reason we will not
        put in writing invites a reply nobody can answer honestly in a
        template.

        This test exists so that decision cannot be silently reversed by
        somebody who assumes the missing email is an oversight. If you
        are deliberately adding one, delete this test and say why in the
        commit.
        """
        user = make_supplier("live@example.com")
        make_supplier_profile(user, business_name="Live Traders")

        verification_service.revoke(
            user.id,
            decided_by_user_id=str(make_admin_user().id),
            reason="documents appear altered, watching this account",
        )

        assert mailbox.sent_emails == []

    def test_the_revocation_is_recorded_where_a_regulator_would_look(
        self, app, db_session, mailbox, make_supplier, make_supplier_profile, make_admin_user
    ):
        """NOT SENDING AN EMAIL IS NOT THE SAME AS NOT RECORDING IT.

        "Why was this supplier removed, by whom, and when" has to be
        answerable years later. The audit row is where that lives, and
        it carries the FROM status as well as the TO -- "became
        unverified" and "was never verified" are different facts, and
        only the first one is what the question is about.
        """
        from src.extensions import db as _db

        user = make_supplier("live@example.com")
        make_supplier_profile(user, business_name="Live Traders")
        staff = make_admin_user()

        verification_service.revoke(
            user.id, decided_by_user_id=str(staff.id), reason="Documents expired."
        )

        row = _db.session.execute(
            _db.text(
                "SELECT user_id, metadata FROM security.audit_events "
                "WHERE event_name = 'verification.supplier_revoked' "
                "ORDER BY timestamp DESC LIMIT 1"
            )
        ).fetchone()

        assert row is not None, "a revocation left no audit trail"
        assert str(row[0]) == str(staff.id)
        assert row[1]["reason"] == "Documents expired."
        assert row[1]["from_status"] == "verified"
        assert row[1]["to_status"] == "unverified"


class TestTheLadder:
    def test_nothing_is_sent_before_the_first_rung_is_due(
        self, app, db_session, mailbox, hidden_supplier
    ):
        hidden_supplier()

        sweep.run()

        assert mailbox.sent_emails == []

    def test_the_first_rung_fires_after_a_day(self, app, db_session, mailbox, hidden_supplier):
        _, profile = hidden_supplier()
        _age(profile, days=1, hours=1)

        sweep.run()

        assert len(mailbox.sent_emails) == 1
        assert profile.verification_reminder_stage == 1

    def test_it_does_not_send_the_same_rung_twice(self, app, db_session, mailbox, hidden_supplier):
        """The sweep runs every six hours. Without the stamp it would
        re-send to the same supplier on every tick, forever."""
        _, profile = hidden_supplier()
        _age(profile, days=1, hours=1)

        sweep.run()
        sweep.run()
        sweep.run()

        assert len(mailbox.sent_emails) == 1

    def test_the_ladder_stops_after_three(self, app, db_session, mailbox, hidden_supplier):
        """THREE RUNGS, THEN SILENCE. The thing being waited on is OUR
        decision; a fourth email is nagging."""
        _, profile = hidden_supplier()

        for _ in range(6):
            _age(profile, days=30)
            sweep.run()

        assert len(mailbox.sent_emails) == verification_emails.LADDER_LENGTH
        assert profile.verification_reminder_stage == verification_emails.LADDER_LENGTH

    def test_the_last_rung_blames_us_not_them(self, app, db_session, mailbox, hidden_supplier):
        """By day seven the likely problem is on our side, and the
        wording has to say so rather than implying they forgot
        something."""
        _, profile = hidden_supplier()
        for _ in range(3):
            _age(profile, days=30)
            sweep.run()

        last = mailbox.sent_emails[-1]["html_body"].lower()
        assert "on our side" in last or "waiting on us" in last

    def test_a_verified_supplier_is_never_reminded(
        self, app, db_session, mailbox, make_supplier, make_supplier_profile
    ):
        user = make_supplier("live@example.com")
        profile = make_supplier_profile(user, business_name="Live Traders")
        _age(profile, days=90)

        sweep.run()

        assert mailbox.sent_emails == []

    def test_deploy_day_is_not_a_mailstorm(self, app, db_session, mailbox, hidden_supplier):
        """An existing supplier with an ancient created_at and no
        sent_at gets rung ONE, then waits the real interval like
        everybody else -- not all three in the first few sweeps."""
        _, profile = hidden_supplier()
        profile.verification_reminder_sent_at = None
        profile.created_at = utcnow() - timedelta(days=400)
        db.session.commit()

        sweep.run()
        sweep.run()

        assert len(mailbox.sent_emails) == 1
        assert profile.verification_reminder_stage == 1


class TestTheClockResets:
    def test_approving_clears_the_ladder(
        self, app, db_session, mailbox, hidden_supplier, make_admin_user
    ):
        _, profile = hidden_supplier()
        _age(profile, days=1, hours=1)
        sweep.run()
        assert profile.verification_reminder_stage == 1

        verification_service.approve(
            profile.supplier_id, decided_by_user_id=str(make_admin_user().id), reason="ok"
        )

        assert profile.verification_reminder_stage == 0
        assert profile.verification_reminder_sent_at is None

    def test_revoking_restarts_the_clock_from_now(
        self, app, db_session, mailbox, make_supplier, make_supplier_profile, make_admin_user
    ):
        """WITHOUT THIS, a supplier verified two years ago and revoked
        today would have an ancient clock and receive the entire ladder
        in the first sweep after the revocation."""
        user = make_supplier("live@example.com")
        profile = make_supplier_profile(user, business_name="Live Traders")
        profile.created_at = utcnow() - timedelta(days=400)
        db.session.commit()

        verification_service.revoke(
            user.id, decided_by_user_id=str(make_admin_user().id), reason="internal"
        )
        mailbox.clear()

        sweep.run()

        assert mailbox.sent_emails == []
        assert profile.verification_reminder_stage == 0
