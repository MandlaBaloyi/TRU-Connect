"""
THE CURTAIN, tested as behaviour rather than as structure.

tests/architecture/test_verification_curtain.py proves the rule cannot
be BYPASSED. This file proves it actually WORKS -- that an unverified
supplier is genuinely absent from what a business can see, and that
approving one turns everything on at once.

THE TWO HALVES MATTER EQUALLY. A curtain that hides too little lets an
unvetted supplier take somebody's money. A curtain that hides too much
erases a business's own order history the day a supplier is revoked.
Both are tested here, because the second failure is the one that looks
like a bug report from a customer rather than a security incident.
"""
from __future__ import annotations

import pytest

from src.domains.supplier.supplier_profile.models.supplier_profile import (
    SupplierVerificationStatus,
)
from src.domains.verification.services import verification_service
from src.extensions import db


@pytest.fixture()
def make_hidden_supplier(make_supplier, make_supplier_profile):
    """A supplier who has done all the work and cannot be seen.

    The state V2_03 Part 4.5 describes: profile complete, catalogue
    built, nobody can find them.
    """

    def _make(email: str = "hidden@example.com", business_name: str = "Hidden Wholesale"):
        user = make_supplier(email)
        profile = make_supplier_profile(
            user,
            business_name=business_name,
            verification_status=SupplierVerificationStatus.UNVERIFIED,
        )
        return user, profile

    return _make


class TestSearch:
    def test_an_unverified_supplier_is_not_findable(self, app, db_session, make_hidden_supplier):
        from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
            SupplierProfileRepository,
        )

        make_hidden_supplier(business_name="Zenzele Wholesale")

        results = SupplierProfileRepository.search_by_name_prefix("Zenzele")

        assert results == []

    def test_the_same_supplier_appears_once_approved(
        self, app, db_session, make_hidden_supplier, make_admin_user
    ):
        from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
            SupplierProfileRepository,
        )

        user, _ = make_hidden_supplier(business_name="Zenzele Wholesale")
        assert SupplierProfileRepository.search_by_name_prefix("Zenzele") == []

        verification_service.approve(
            user.id, decided_by_user_id=str(make_admin_user().id), reason="Certificate checked."
        )

        results = SupplierProfileRepository.search_by_name_prefix("Zenzele")
        assert len(results) == 1
        assert results[0].business_name == "Zenzele Wholesale"

    def test_the_limit_is_not_eaten_by_hidden_suppliers(
        self, app, db_session, make_supplier, make_supplier_profile, make_hidden_supplier
    ):
        """THE BUG THAT MOTIVATED FILTERING IN SQL RATHER THAN IN PYTHON.

        .limit() runs in the database. Filtering afterwards in Python
        would let hidden suppliers consume the limit, so a search for
        20 could return 1 -- and it would look like a ranking problem,
        not a visibility one.
        """
        for i in range(3):
            make_hidden_supplier(email=f"hidden{i}@example.com", business_name=f"Acme Hidden {i}")
        visible_user = make_supplier("visible@example.com")
        make_supplier_profile(
            visible_user,
            business_name="Acme Visible",
            verification_status=SupplierVerificationStatus.VERIFIED,
        )

        from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
            SupplierProfileRepository,
        )

        results = SupplierProfileRepository.search_by_name_prefix("Acme", limit=2)

        assert [r.business_name for r in results] == ["Acme Visible"]


class TestStorefront:
    def test_an_unverified_supplier_has_no_storefront(self, app, db_session, make_hidden_supplier):
        from src.domains.network.connections.services.storefront import catalog_service
        from src.domains.network.connections.services.errors import SupplierNotFoundError

        _, profile = make_hidden_supplier()

        with pytest.raises(SupplierNotFoundError):
            catalog_service.list_supplier_products("00000000-0000-0000-0000-000000000001", profile.id)

    def test_the_refusal_does_not_reveal_that_they_exist(
        self, app, db_session, make_hidden_supplier
    ):
        """A buyer gets the same answer for "pending supplier" and "no
        such supplier". Telling them apart would leak which accounts
        have applied and not yet passed."""
        from src.domains.network.connections.services.storefront import catalog_service
        from src.domains.network.connections.services.errors import SupplierNotFoundError

        _, profile = make_hidden_supplier()
        business_id = "00000000-0000-0000-0000-000000000001"

        with pytest.raises(SupplierNotFoundError) as hidden:
            catalog_service.list_supplier_products(business_id, profile.id)
        with pytest.raises(SupplierNotFoundError) as absent:
            catalog_service.list_supplier_products(
                business_id, "00000000-0000-0000-0000-0000000000ff"
            )

        assert str(hidden.value) == str(absent.value)


class TestTheSupplierSideIsUntouched:
    """THE HALF THAT IS EASY TO GET WRONG. The curtain hides a supplier
    from BUYERS. It must never hide a supplier from themselves."""

    def test_they_still_see_their_own_profile(self, app, db_session, make_hidden_supplier):
        from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
            SupplierProfileRepository,
        )

        user, profile = make_hidden_supplier()

        assert SupplierProfileRepository.get_by_supplier_id(user.id) is not None
        assert SupplierProfileRepository.get_by_id(profile.id) is not None

    def test_the_status_message_is_encouraging_not_scolding(
        self, app, db_session, make_hidden_supplier
    ):
        """V2_03 Part 4.5: "your shop is ready and nobody can see it
        yet", never "you are not verified" -- the second reads as
        rejection to somebody who just spent an hour building a
        catalogue."""
        user, _ = make_hidden_supplier()

        status = verification_service.get_status(user.id)

        assert status["visibleToBuyers"] is False
        assert "ready" in status["headline"].lower()
        assert "not verified" not in status["headline"].lower()


class TestApprovalAndRevocation:
    def test_approve_requires_a_reason(self, app, db_session, make_hidden_supplier, make_admin_user):
        from src.core.exceptions import ValidationError

        user, _ = make_hidden_supplier()

        with pytest.raises(ValidationError):
            verification_service.approve(
                user.id, decided_by_user_id=str(make_admin_user().id), reason="   "
            )

    def test_revoking_hides_them_again(self, app, db_session, make_supplier, make_supplier_profile, make_admin_user):
        from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
            SupplierProfileRepository,
        )

        user = make_supplier("live@example.com")
        make_supplier_profile(user, business_name="Live Traders")
        assert SupplierProfileRepository.search_by_name_prefix("Live") != []

        verification_service.revoke(
            user.id, decided_by_user_id=str(make_admin_user().id), reason="Documents expired."
        )

        assert SupplierProfileRepository.search_by_name_prefix("Live") == []

    def test_revoking_does_not_touch_their_work(
        self, app, db_session, make_supplier, make_supplier_profile, make_admin_user
    ):
        """A revocation is not a deletion. Their catalogue, name and
        settings survive -- only visibility changes."""
        user = make_supplier("live@example.com")
        profile = make_supplier_profile(user, business_name="Live Traders")
        profile_id = profile.id

        verification_service.revoke(
            user.id, decided_by_user_id=str(make_admin_user().id), reason="Documents expired."
        )
        db.session.expire_all()

        from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
            SupplierProfileRepository,
        )

        still_there = SupplierProfileRepository.get_by_id(profile_id)
        assert still_there is not None
        assert still_there.business_name == "Live Traders"
        assert still_there.is_deleted is False


@pytest.fixture()
def make_admin_user(make_user, db_session):
    from src.domains.auth.models.user import UserRole, VerificationStatus

    def _make(email: str = "staff@truconnect.co.za"):
        user = make_user(
            email, role=UserRole.ADMIN, verification_status=VerificationStatus.VERIFIED
        )
        db_session.commit()
        return user

    return _make
