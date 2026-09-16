"""
The gate in front of a brand-new shop.

WHAT THESE DEFEND, worst consequence first:

  A BRAND-NEW ACCOUNT MUST GET AN ANSWER, NOT AN ERROR. The very first
  authenticated call a new business makes is this one, before any
  profile row exists. A 404 or a 500 here is a signup that dead-ends on
  the screen after the OTP.

  THE TWO REQUIRED STEPS GATE; THE THIRD NEVER DOES. Step three needs a
  location permission, and blocking a new account behind a permission
  dialog is the most expensive place in an app to lose somebody
  (V2_18 4.3). If requiredComplete ever starts waiting on a location,
  every shop that declines the prompt is stuck outside their own
  dashboard.

  THE STEPS MEAN WHAT THE ENGINE READS. The whole reason this lives in
  demand/ is that "which answers are mandatory" and "which columns the
  engine reads" must be one list. The last test holds that.

  THE ROUTE PINS A ROLE. A supplier has no buys_categories and no
  restock rhythm, so an unpinned route would hand them a confident
  description of a shop they are not.
"""
from __future__ import annotations

from itertools import count

import pytest

from src.domains.business.demand.services import setup_service
from src.extensions import db

_seq = count()


@pytest.fixture()
def shop(make_business):
    """A verified business with no profile answers at all."""
    return make_business(f"setup{next(_seq)}@example.com")


def _profile_for(user_id):
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    return BusinessProfileRepository.get_or_create_for_business(user_id)


class TestAnEmptyShop:
    def test_a_business_with_no_profile_row_gets_every_step_unanswered(self, app, shop):
        """NOT AN ERROR. The profile row is created lazily, so the
        state a new account is actually in is "no row", and that is
        precisely the state this endpoint exists to describe."""
        state = setup_service.setup_state(shop.id)

        assert state["requiredComplete"] is False
        assert state["isComplete"] is False
        assert state["nextStep"] == setup_service.STEP_WHAT_YOU_BUY
        assert all(done is False for done in state["steps"].values())

    def test_next_step_is_the_first_one_missing_not_an_arbitrary_one(self, app, shop):
        """The app never decides the order. If it did, the two could
        disagree about it and a person would be sent back to a step
        they already answered."""
        profile = _profile_for(shop.id)
        profile.buys_categories = ["FOOD_GROCERY"]
        db.session.commit()

        assert setup_service.setup_state(shop.id)["nextStep"] == setup_service.STEP_HOW_YOU_BUY


class TestWhatCountsAsAnsweredS:
    def test_how_you_buy_needs_both_answers(self, app, shop):
        """Rhythm sets WHEN the feed should press, spend sets what SIZE
        of basket it may show. Neither substitutes for the other, and a
        shop with one of them gets half a model."""
        from src.domains.business.business_profile.models.business_profile import RestockRhythm

        profile = _profile_for(shop.id)
        profile.restock_rhythm = RestockRhythm.WEEKLY
        db.session.commit()

        assert setup_service.setup_state(shop.id)["steps"][setup_service.STEP_HOW_YOU_BUY] is False


class TestTheSkippableStepNeverGates:
    def test_required_is_complete_without_a_location(self, app, shop):
        """THE PROPERTY THE WHOLE GATE RESTS ON. If this ever fails,
        every shop that declines the location prompt is locked out of
        their own dashboard."""
        from src.domains.business.business_profile.models.business_profile import (
            RestockRhythm,
            WeeklySpendBand,
        )

        profile = _profile_for(shop.id)
        profile.buys_categories = ["FOOD_GROCERY"]
        profile.restock_rhythm = RestockRhythm.WEEKLY
        profile.weekly_spend_band = WeeklySpendBand.R500_TO_2000
        db.session.commit()

        state = setup_service.setup_state(shop.id)

        assert state["requiredComplete"] is True, "a missing location must never block the gate"
        assert state["isComplete"] is False, "but it is still honestly unfinished"
        assert state["nextStep"] == setup_service.STEP_WHERE_YOU_ARE

    def test_a_full_answer_is_complete(self, app, shop):
        from src.domains.business.business_profile.models.business_profile import (
            RestockRhythm,
            WeeklySpendBand,
        )

        profile = _profile_for(shop.id)
        profile.buys_categories = ["FOOD_GROCERY"]
        profile.restock_rhythm = RestockRhythm.DAILY
        profile.weekly_spend_band = WeeklySpendBand.R2000_TO_5000
        profile.latitude, profile.longitude = -23.8890, 29.7350
        db.session.commit()

        state = setup_service.setup_state(shop.id)

        assert state["isComplete"] is True
        assert state["nextStep"] is None


class TestTheRoute:
    def test_a_supplier_is_refused(self, client, make_supplier):
        from flask_jwt_extended import create_access_token

        user = make_supplier()
        token = create_access_token(
            identity=str(user.id), additional_claims={"role": "supplier"}
        )

        response = client.get(
            "/api/v1/business/setup-state", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

    def test_an_anonymous_caller_is_refused(self, client):
        assert client.get("/api/v1/business/setup-state").status_code == 401

    def test_a_brand_new_business_gets_200(self, client, shop):
        """The first authenticated call of a new account's life."""
        from flask_jwt_extended import create_access_token

        token = create_access_token(
            identity=str(shop.id), additional_claims={"role": "business"}
        )

        response = client.get(
            "/api/v1/business/setup-state", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.get_json()["data"]["requiredComplete"] is False


class TestTheStepsMatchWhatTheEngineReads:
    """THE DRIFT THIS PREVENTS HAS NO SYMPTOM.

    If a step stops corresponding to a field the engine reads, nothing
    raises: the flow keeps collecting answers, the gate keeps opening,
    and the shops coming through it are simply worse served than the
    ones that came through last month. Nobody would connect the two.
    """

    def test_every_declared_step_has_something_deciding_it(self):
        """A step in ALL_STEPS that _completed never sets would report
        as missing from the dict, and the app would read `undefined`
        for it -- which is falsy, so the person is sent to a step that
        can never be satisfied."""
        from src.domains.business.demand.signals.declared import DeclaredSignals

        decided = setup_service._completed(DeclaredSignals())

        assert set(decided) == set(setup_service.ALL_STEPS)

    def test_every_field_it_reads_is_still_a_signal_the_engine_has(self):
        """A renamed or deleted DeclaredSignals field would not raise
        here -- it would read as a missing attribute and the step would
        quietly evaluate False forever, so the gate would never open
        and nobody would know which field did it."""
        import inspect

        from src.domains.business.demand.signals.declared import DeclaredSignals

        source = inspect.getsource(setup_service._completed)
        fields = set(DeclaredSignals.__dataclass_fields__)

        read_here = {
            name for name in fields | {"has_location"} if f"signals.{name}" in source
        }
        assert read_here, "this test is only meaningful if it found the reads"

        for name in read_here:
            assert name in fields, (
                f"setup_service reads signals.{name}, which DeclaredSignals no longer has. "
                "Either the engine stopped reading it -- in which case the step should go -- "
                "or it was renamed and this flow now collects a field nobody uses."
            )

    def test_required_steps_are_a_subset_of_all_steps(self):
        """Requiring a step that does not exist would make
        requiredComplete raise a KeyError on the first call of a new
        account's life."""
        assert set(setup_service.REQUIRED_STEPS) <= set(setup_service.ALL_STEPS)
        assert setup_service.STEP_WHERE_YOU_ARE not in setup_service.REQUIRED_STEPS, (
            "step three is skippable -- requiring it locks out every shop "
            "that declines the location prompt"
        )
