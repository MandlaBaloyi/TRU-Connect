"""
The loop the feed never closed.

Inviting a supplier is the most effort a shopkeeper can put into this
platform: they leave the app, message somebody they already trade with,
and talk them into signing up. Until this rail existed the app said
nothing afterwards -- no "they joined", no "still waiting". The single
most invested action a user can take had no reply.

WHAT THESE DEFEND, worst consequence first:

  THE CURTAIN DOES NOT BEND FOR IT. An invited supplier who registered
  but has not been verified must NOT appear. A rail is exactly the kind
  of well-meaning special case that quietly relaxes a security rule,
  and V2_15 Part 12 is explicit that the curtain never relaxes -- not
  for sponsorship, not for demo, not for a thin rail.

  NO NAMES IN THE WAITING COUNT. Saying "waiting on joe@example.com"
  would confirm whether a particular address has an account. A number
  cannot.

  ONE CARD IS A COMPLETE THOUGHT HERE, unlike every other rail, and the
  test pins that so somebody does not later "fix" it by applying
  MIN_ITEMS_PER_RAIL for consistency.
"""
from __future__ import annotations

import uuid
from datetime import timedelta
from itertools import count

import pytest

from src.core.base_model import utcnow
from src.domains.network.community.business import sections
from src.extensions import db

_seq = count()


@pytest.fixture()
def invite(db_session):
    """An invitation this business sent to a supplier, in any state."""
    from src.domains.network.connections.models.network_invitation import (
        InvitationStatus,
        InvitedRole,
        NetworkInvitation,
    )

    def _make(business_user, *, status, invited_user_id=None):
        n = next(_seq)
        invitation = NetworkInvitation(
            inviter_id=business_user.id,
            invited_role=InvitedRole.SUPPLIER,
            invited_email=f"invited{n}@example.com",
            ticket_hash=f"hash-{uuid.uuid4().hex}",
            expires_at=utcnow() + timedelta(days=14),
            status=status,
            invited_user_id=invited_user_id,
        )
        db.session.add(invitation)
        db.session.commit()
        return invitation

    return _make


@pytest.fixture()
def supplier_account(db_session):
    """A supplier user plus profile, verified or not."""
    from src.domains.auth.models.user import User, UserRole, VerificationStatus
    from src.domains.supplier.supplier_profile.models.supplier_profile import (
        SupplierProfile,
        SupplierVerificationStatus,
    )

    def _make(name, *, verified=True):
        n = next(_seq)
        user = User(
            id=uuid.uuid4(),
            email=f"inv-sup{n}@example.com",
            password_hash="x",
            role=UserRole.SUPPLIER,
            verification_status=VerificationStatus.VERIFIED,
        )
        db.session.add(user)
        db.session.flush()
        profile = SupplierProfile(
            supplier_id=user.id,
            business_name=name,
            verification_status=(
                SupplierVerificationStatus.VERIFIED
                if verified
                else SupplierVerificationStatus.UNVERIFIED
            ),
        )
        db.session.add(profile)
        db.session.commit()
        return user, profile

    return _make


class TestTheLoopCloses:
    def test_a_supplier_who_joined_and_got_verified_appears(
        self, app, db_session, make_business, invite, supplier_account
    ):
        from src.domains.network.connections.models.network_invitation import InvitationStatus

        business = make_business("inviter-a@example.com")
        user, _ = supplier_account("Thabo Beverages")
        invite(business, status=InvitationStatus.REGISTERED, invited_user_id=user.id)

        section = sections.invited_suppliers(business.id)

        assert section is not None
        assert [s["businessName"] for s in section["suppliers"]] == ["Thabo Beverages"]

    def test_one_card_is_enough(
        self, app, db_session, make_business, invite, supplier_account
    ):
        """DELIBERATELY UNLIKE EVERY OTHER RAIL. MIN_ITEMS_PER_RAIL is 3
        because a DISCOVERY rail with two cards implies a thin
        catalogue. "Thabo joined because you invited them" is a complete
        thought on its own, and padding it would be the mistake."""
        from src.domains.network.connections.models.network_invitation import InvitationStatus

        business = make_business("inviter-b@example.com")
        user, _ = supplier_account("Only One")
        invite(business, status=InvitationStatus.REGISTERED, invited_user_id=user.id)

        section = sections.invited_suppliers(business.id)

        assert len(section["suppliers"]) == 1

    def test_a_business_that_invited_nobody_gets_no_rail(
        self, app, db_session, make_business
    ):
        business = make_business("inviter-c@example.com")

        assert sections.invited_suppliers(business.id) is None


class TestTheCurtainDoesNotBend:
    def test_an_invited_supplier_who_is_not_verified_stays_hidden(
        self, app, db_session, make_business, invite, supplier_account
    ):
        """THE ONE THAT MATTERS. A rail is exactly the kind of
        well-meaning special case that quietly relaxes a security rule.
        """
        from src.domains.network.connections.models.network_invitation import InvitationStatus

        business = make_business("inviter-d@example.com")
        user, _ = supplier_account("Pending Co", verified=False)
        invite(business, status=InvitationStatus.REGISTERED, invited_user_id=user.id)

        assert sections.invited_suppliers(business.id) is None

    def test_a_verified_one_still_shows_when_an_unverified_one_exists(
        self, app, db_session, make_business, invite, supplier_account
    ):
        """The gate removes a candidate; it does not kill the rail."""
        from src.domains.network.connections.models.network_invitation import InvitationStatus

        business = make_business("inviter-e@example.com")
        hidden, _ = supplier_account("Pending Co", verified=False)
        shown, _ = supplier_account("Verified Co", verified=True)
        invite(business, status=InvitationStatus.REGISTERED, invited_user_id=hidden.id)
        invite(business, status=InvitationStatus.REGISTERED, invited_user_id=shown.id)

        section = sections.invited_suppliers(business.id)

        assert [s["businessName"] for s in section["suppliers"]] == ["Verified Co"]


class TestTheWaitingCountNamesNobody:
    def test_pending_invitations_are_counted_not_listed(
        self, app, db_session, make_business, invite, supplier_account
    ):
        from src.domains.network.connections.models.network_invitation import InvitationStatus

        business = make_business("inviter-f@example.com")
        user, _ = supplier_account("Verified Co")
        invite(business, status=InvitationStatus.REGISTERED, invited_user_id=user.id)
        invite(business, status=InvitationStatus.PENDING)
        invite(business, status=InvitationStatus.PENDING)

        section = sections.invited_suppliers(business.id)

        assert section["subtitle"] == "2 more invitations still waiting"
        assert "@" not in section["subtitle"], "an email address must never reach the subtitle"

    def test_one_waiting_reads_as_one(
        self, app, db_session, make_business, invite, supplier_account
    ):
        from src.domains.network.connections.models.network_invitation import InvitationStatus

        business = make_business("inviter-g@example.com")
        user, _ = supplier_account("Verified Co")
        invite(business, status=InvitationStatus.REGISTERED, invited_user_id=user.id)
        invite(business, status=InvitationStatus.PENDING)

        assert sections.invited_suppliers(business.id)["subtitle"] == (
            "1 more invitation still waiting"
        )

    def test_nothing_waiting_says_something_useful_instead(
        self, app, db_session, make_business, invite, supplier_account
    ):
        from src.domains.network.connections.models.network_invitation import InvitationStatus

        business = make_business("inviter-h@example.com")
        user, _ = supplier_account("Verified Co")
        invite(business, status=InvitationStatus.COMPLETED, invited_user_id=user.id)

        assert sections.invited_suppliers(business.id)["subtitle"] == (
            "Suppliers you brought to TruConnect"
        )
