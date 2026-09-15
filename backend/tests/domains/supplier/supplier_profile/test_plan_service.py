"""
Setting a supplier's plan.

WHAT THESE DEFEND, worst consequence first:

  AN EXPIRY IN THE PAST IS REFUSED, NOT ACCEPTED-AND-IGNORED.
  tier_rules.effective_tier reads a lapsed plan as FREE, so accepting
  one would mean the command reporting success while the supplier's
  reach never moved -- the worst possible outcome for somebody who has
  just been billed. A mistyped year is the likeliest cause.

  A PLAN IS NEVER A CURTAIN. Nothing here touches verification_status.
  Reach and visibility are different questions and the moment they are
  confused, money buys the right to be seen -- which V2_16 forbids in
  the strongest terms it has.

  THE EXPIRY IS ALWAYS ASSIGNED, never left behind. Moving somebody
  from a time-boxed PARTNER deal to FREE and leaving last year's expiry
  on the row leaves the next reader unable to tell whether the plan
  lapsed or was changed.

  A REASON IS REQUIRED. The record is the point. "Who put this supplier
  on MAX, and on what basis" gets asked, most often by the supplier who
  believes a competitor got something they did not.
"""
from __future__ import annotations

from datetime import timedelta
from itertools import count

import pytest

from src.core.base_model import utcnow
from src.core.exceptions import ValidationError
from src.domains.network.community.placement import tier_rules
from src.domains.supplier.supplier_profile.models.supplier_profile import (
    SupplierPlanTier,
    SupplierVerificationStatus,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.domains.supplier.supplier_profile.services import plan_service

_seq = count()

DECIDER = "11111111-1111-1111-1111-111111111111"


@pytest.fixture()
def supplier(make_supplier):
    return make_supplier(f"plan{next(_seq)}@example.com")


class TestSettingAPlan:
    def test_it_moves_the_tier_and_the_cap_follows(self, app, supplier):
        plan_service.set_plan(
            supplier.id, tier="MAX", decided_by_user_id=DECIDER, reason="Pilot partner."
        )

        profile = SupplierProfileRepository.get_by_supplier_id(supplier.id)
        assert profile.plan_tier is SupplierPlanTier.MAX
        assert tier_rules.absolute_cap(tier_rules.effective_tier(profile)) == 5

    def test_lowercase_is_accepted(self, app, supplier):
        """Somebody typing at a terminal at 11pm. The value is
        normalised rather than refused, because refusing teaches
        nothing and costs a retype."""
        plan_service.set_plan(
            supplier.id, tier="pro", decided_by_user_id=DECIDER, reason="Signed up."
        )

        assert (
            SupplierProfileRepository.get_by_supplier_id(supplier.id).plan_tier
            is SupplierPlanTier.PRO
        )

    def test_an_unknown_tier_is_refused_with_the_options(self, app, supplier):
        with pytest.raises(ValidationError) as caught:
            plan_service.set_plan(
                supplier.id, tier="PLATINUM", decided_by_user_id=DECIDER, reason="x"
            )

        assert "PARTNER" in str(caught.value), "say what IS allowed, not just what is not"

    def test_a_blank_reason_is_refused(self, app, supplier):
        with pytest.raises(ValidationError):
            plan_service.set_plan(
                supplier.id, tier="MAX", decided_by_user_id=DECIDER, reason="   "
            )


class TestExpiry:
    def test_a_future_expiry_is_kept_and_the_plan_applies(self, app, supplier):
        until = utcnow() + timedelta(days=30)

        plan_service.set_plan(
            supplier.id,
            tier="PARTNER",
            decided_by_user_id=DECIDER,
            reason="Three-month pilot.",
            expires_at=until,
        )

        profile = SupplierProfileRepository.get_by_supplier_id(supplier.id)
        assert profile.plan_expires_at is not None
        assert tier_rules.effective_tier(profile) == "PARTNER"

    def test_an_expiry_in_the_past_is_refused(self, app, supplier):
        """IT WOULD SILENTLY DO NOTHING. effective_tier reads a lapsed
        plan as FREE, so this would report success while the supplier's
        reach stayed exactly where it was."""
        with pytest.raises(ValidationError):
            plan_service.set_plan(
                supplier.id,
                tier="MAX",
                decided_by_user_id=DECIDER,
                reason="Backdated by mistake.",
                expires_at=utcnow() - timedelta(days=1),
            )

    def test_changing_plan_clears_a_previous_expiry(self, app, supplier):
        """Otherwise a supplier moved off a time-boxed deal keeps last
        year's date on their row, and the next person to read it cannot
        tell whether the plan lapsed or was changed."""
        plan_service.set_plan(
            supplier.id,
            tier="PARTNER",
            decided_by_user_id=DECIDER,
            reason="Pilot.",
            expires_at=utcnow() + timedelta(days=30),
        )

        plan_service.set_plan(
            supplier.id, tier="FREE", decided_by_user_id=DECIDER, reason="Pilot ended."
        )

        profile = SupplierProfileRepository.get_by_supplier_id(supplier.id)
        assert profile.plan_expires_at is None


class TestAPlanIsNotACurtain:
    def test_it_does_not_touch_verification(self, app, supplier):
        """THE BOUNDARY V2_16 DEFENDS MOST STRONGLY. A tier buys reach
        beyond what you have earned; it cannot buy the right to be seen
        at all."""
        before = SupplierProfileRepository.get_by_supplier_id(supplier.id).verification_status

        plan_service.set_plan(
            supplier.id, tier="MAX", decided_by_user_id=DECIDER, reason="Paid."
        )

        after = SupplierProfileRepository.get_by_supplier_id(supplier.id).verification_status
        assert after is before

    def test_an_unverified_supplier_can_be_put_on_a_plan(
        self, app, make_supplier, db_session
    ):
        """DELIBERATELY ALLOWED. A deal can be negotiated before
        onboarding finishes, and the plan should simply be waiting when
        somebody approves them. Reaching for the VISIBILITY-gated
        lookup here would hide a supplier from the staff member
        handling their account."""
        user = make_supplier(f"unverified{next(_seq)}@example.com")
        profile = SupplierProfileRepository.get_by_supplier_id(user.id)
        profile.verification_status = SupplierVerificationStatus.UNVERIFIED
        db_session.commit()

        plan_service.set_plan(
            user.id, tier="PARTNER", decided_by_user_id=DECIDER, reason="Signed before launch."
        )

        refreshed = SupplierProfileRepository.get_by_supplier_id(user.id)
        assert refreshed.plan_tier is SupplierPlanTier.PARTNER
        assert refreshed.verification_status is SupplierVerificationStatus.UNVERIFIED
