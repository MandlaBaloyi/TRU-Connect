"""
What a supplier IS, and what they pay for.

TWO COLUMNS, TWO DIFFERENT JOBS, and the tests that matter are about
the defaults rather than the storage.

supplier_kind EXISTS BECAUSE A NAME FILTER IS WRONG IN BOTH DIRECTIONS.
The real database is the argument: "Qwen Wholesale" and "Lepelle
Wholesalers" would match a keyword search, "Seshego Cash & Carry" is a
wholesaler and would not, and a retailer trading as "Wholesale Beauty
Supplies" would be listed having done nothing wrong. A screen somebody
can enter by renaming their business is not a filter.

plan_tier IS REACH, NOT PERMISSION (V2_16). The test that a FREE
supplier is a full member is in the architecture suite and in the feed
suites, where it belongs -- what is pinned here is that FREE is the
default, so nobody has to be assigned a plan to exist.
"""
from __future__ import annotations

import uuid

import pytest

from src.domains.supplier.supplier_profile.models.supplier_profile import (
    SupplierKind,
    SupplierPlanTier,
    SupplierProfile,
)
from src.extensions import db


@pytest.fixture()
def profile(app, db_session, make_supplier):
    """A supplier profile created the ordinary way, with nothing set."""
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )

    user = make_supplier()
    return SupplierProfileRepository.get_or_create_for_supplier(
        user.id, default_name="Plain Supplier"
    )


class TestTheDefaultsAreTheHonestState:
    def test_a_new_supplier_is_unspecified_not_a_retailer(self, profile):
        """UNSPECIFIED IS A REAL ANSWER. Every supplier already in the
        database is genuinely unspecified, and defaulting them to a
        guess would be inventing a fact about somebody's business."""
        assert profile.supplier_kind is SupplierKind.UNSPECIFIED

    def test_a_new_supplier_is_free(self, profile):
        """Nobody has to be assigned a plan in order to exist."""
        assert profile.plan_tier is SupplierPlanTier.FREE

    def test_a_free_plan_does_not_expire(self, profile):
        """NULL means "does not expire", which is right for FREE and for
        an open-ended subscription. Only a trial or a PARTNER agreement
        sets it."""
        assert profile.plan_expires_at is None


class TestKindIsStatedNotGuessed:
    @pytest.mark.parametrize(
        "business_name",
        ["Qwen Wholesale", "Lepelle Wholesalers", "Wholesale Beauty Supplies"],
    )
    def test_the_word_wholesale_in_a_name_changes_nothing(
        self, app, db_session, make_supplier, business_name
    ):
        """THE TRAP THIS COLUMN EXISTS TO AVOID. Three real-looking
        names, none of which should make a business a wholesaler."""
        from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
            SupplierProfileRepository,
        )

        user = make_supplier()
        created = SupplierProfileRepository.get_or_create_for_supplier(
            user.id, default_name=business_name
        )

        assert created.supplier_kind is SupplierKind.UNSPECIFIED

    def test_a_wholesaler_without_the_word_is_still_a_wholesaler(
        self, app, db_session, make_supplier
    ):
        """The other direction: "Seshego Cash & Carry" says nothing in
        its name and is exactly what Explore should list."""
        from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
            SupplierProfileRepository,
        )

        user = make_supplier()
        created = SupplierProfileRepository.get_or_create_for_supplier(
            user.id, default_name="Seshego Cash & Carry"
        )
        created.supplier_kind = SupplierKind.WHOLESALER
        db.session.commit()

        found = SupplierProfile.query.filter_by(
            supplier_kind=SupplierKind.WHOLESALER, is_deleted=False
        ).all()

        assert created.id in [p.id for p in found]


class TestTheEnumsRoundTripThroughPostgres:
    def test_every_kind_can_be_stored_and_read_back(self, profile):
        """NAME == VALUE on both enums, because SQLAlchemy persists a
        member's NAME rather than its .value -- a mismatch this project
        has already had to correct once (ConnectionRequestStatus)."""
        for kind in SupplierKind:
            profile.supplier_kind = kind
            db.session.commit()
            db.session.refresh(profile)
            assert profile.supplier_kind is kind

    def test_every_tier_can_be_stored_and_read_back(self, profile):
        for tier in SupplierPlanTier:
            profile.plan_tier = tier
            db.session.commit()
            db.session.refresh(profile)
            assert profile.plan_tier is tier

    def test_name_and_value_match_on_both(self):
        """Pinned directly, so a future member added with a lowercase
        value fails here rather than in production."""
        for member in list(SupplierKind) + list(SupplierPlanTier):
            assert member.name == member.value
