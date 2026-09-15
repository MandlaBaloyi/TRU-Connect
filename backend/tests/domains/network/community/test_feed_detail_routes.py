"""
The screens behind the feed's arrows.

WHAT THESE DEFEND, worst consequence first:

  THE SCREEN MUST AGREE WITH THE RAIL IT OPENED FROM. A "see all" that
  ranked differently is a bug the reader sees instantly and no unit test
  ever would -- which is why the ranking lives in feed_detail_service
  and both surfaces read it rather than each holding a copy.

  EVERY ROUTE PINS A ROLE. These all answer questions about a SHOP --
  what it bought, what it needs, who is near it -- so a supplier calling
  them would get somebody else's shape of answer or an empty one, which
  is worse than a clean refusal. CLAUDE.md: "authenticated" stopped
  meaning "is a buyer" the moment ADMIN existed.

  THE CEILING MEANS THE SAME THING ON PAGE THREE AS ON PAGE ONE. It is
  applied to the whole set before paging, not per page -- otherwise one
  supplier could hold 40% of every page and far more of the total.

  BUY IT AGAIN IS EXEMPT FROM THE CEILING AT ANY LENGTH. It is the
  shop's own confirmed history (V2_17 Q3).
"""
from __future__ import annotations

from itertools import count

import pytest

from src.extensions import db

_seq = count()


@pytest.fixture()
def business_token(client, make_business):
    """A verified business, and the header that authenticates it."""
    from flask_jwt_extended import create_access_token

    user = make_business(f"detail{next(_seq)}@example.com")
    token = create_access_token(identity=str(user.id), additional_claims={"role": "business"})
    return user, {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def supplier_token(client, make_supplier):
    from flask_jwt_extended import create_access_token

    user = make_supplier()
    token = create_access_token(identity=str(user.id), additional_claims={"role": "supplier"})
    return user, {"Authorization": f"Bearer {token}"}


ENDPOINTS = [
    "/api/v1/community/buy-it-again",
    "/api/v1/community/moving-fast",
    "/api/v1/community/stock-for-you",
    "/api/v1/community/collect-near-you",
    "/api/v1/community/not-ordered-yet",
]


class TestEveryRoutePinsARole:
    @pytest.mark.parametrize("path", ENDPOINTS)
    def test_a_supplier_is_refused(self, client, supplier_token, path):
        """Not an oversight and not unfriendly: every one of these
        answers a question about a SHOP, so a supplier would get an
        empty or wrongly-shaped answer. A clean refusal is the kinder
        failure."""
        _, headers = supplier_token

        response = client.get(path, headers=headers)

        assert response.status_code == 403

    @pytest.mark.parametrize("path", ENDPOINTS)
    def test_an_anonymous_caller_is_refused(self, client, path):
        response = client.get(path)

        assert response.status_code == 401


class TestTheyAnswerForAnEmptyShop:
    @pytest.mark.parametrize("path", ENDPOINTS)
    def test_a_brand_new_business_gets_an_empty_page_not_an_error(
        self, client, business_token, path
    ):
        """A shop that has bought nothing, declared nothing and set no
        location must get a usable empty screen. Returning 404 or 500
        for "you have no history yet" would make the arrow feel broken
        on exactly the day somebody first taps it."""
        _, headers = business_token

        response = client.get(path, headers=headers)

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["hasMore"] is False
        assert data["total"] == 0
        assert data.get("products", data.get("suppliers")) == []


class TestPaging:
    def test_limit_is_clamped_rather_than_refused(self, client, business_token):
        """A caller asking for ten thousand has a different idea of a
        page, not a malicious one. Refusing would break a screen over a
        number nobody chose deliberately."""
        _, headers = business_token

        response = client.get(
            "/api/v1/community/buy-it-again?limit=10000", headers=headers
        )

        assert response.status_code == 200

    def test_nonsense_paging_does_not_500(self, client, business_token):
        _, headers = business_token

        response = client.get(
            "/api/v1/community/buy-it-again?limit=abc&offset=-5", headers=headers
        )

        assert response.status_code == 200


class TestTheScreenAgreesWithTheRail:
    def test_collect_near_you_returns_the_same_suppliers_in_the_same_order(
        self, app, client, business_token, make_supplier, make_supplier_profile
    ):
        """THE PROPERTY THE SERVICE EXISTS FOR. The rail previews five;
        the screen lists them all -- and the first five must be the same
        five, in the same order, or the arrow lied."""
        from src.domains.business.business_profile.repositories.business_profile_repository import (
            BusinessProfileRepository,
        )
        from src.domains.network.community.business import sections

        user, headers = business_token
        profile = BusinessProfileRepository.get_or_create_for_business(user.id)
        profile.latitude, profile.longitude = -23.8890, 29.7350
        db.session.commit()

        for i in range(6):
            # UNIQUE EMAILS: make_supplier defaults to one address, so a
            # loop collides on ix_auth_users_email.
            supplier = make_supplier(f"near{next(_seq)}@example.com")
            make_supplier_profile(
                supplier,
                business_name=f"Near Co {i}",
                collection_latitude=-23.8890 - (i / 500),
                collection_longitude=29.7350,
            )

        rail = sections.collect_near_you(user.id)
        response = client.get("/api/v1/community/collect-near-you", headers=headers)
        screen = response.get_json()["data"]["suppliers"]

        rail_names = [s["businessName"] for s in rail["suppliers"]]
        assert rail_names == [s["businessName"] for s in screen[: len(rail_names)]]
        assert rail["hasMore"] is True, "six suppliers, a rail of five -- there IS more"
