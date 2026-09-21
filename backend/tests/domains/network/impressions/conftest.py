"""
Fixtures for the impressions suite.

A FOURTH COPY OF make_business, AND THAT IS THE CONVENTION HERE RATHER
THAN AN OVERSIGHT. community/, connections/ and orders/ each carry this
same factory verbatim, so promoting it to a shared network/conftest.py
would be a refactor of three existing suites -- each of which would
then need revalidating on a run that takes twenty-four minutes -- for a
six-line saving. If it is ever hoisted, hoist all four together.

THE SUITE LIVES HERE BECAUSE THE CODE DOES. src/domains/network/
impressions/ is a SIBLING of community/, not a child: an impressions
table has rows, and test_community_is_a_composer.py's second rule says
a composer that owns tables has stopped composing. The tests mirror
that.
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def make_business(make_user, db_session):
    from src.domains.auth.models.user import UserRole, VerificationStatus

    def _make(email: str = "business@example.com"):
        user = make_user(
            email, role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED
        )
        db_session.commit()
        return user

    return _make
