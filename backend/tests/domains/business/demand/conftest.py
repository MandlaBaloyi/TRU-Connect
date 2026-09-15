"""Demand engine test fixtures.

Same shape as business_profile's and order_book's own conftests -- the
real create_app("testing") factory and a VERIFIED business user, since
fully_authenticated re-checks status against the database on every
request.

make_business RATHER THAN make_business_user, to match the name the
network and community suites use: these tests exercise the same feed
sections those do, and one concept with two fixture names is how a
test file ends up importing the wrong one.
"""
from __future__ import annotations

import uuid

import pytest

from src import create_app
from src.extensions import db


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def db_session(app):
    return db.session


@pytest.fixture()
def client(app):
    """Added for the setup-state route tests. The rest of this suite
    calls services directly, but a route's ROLE PIN can only be proven
    over HTTP -- calling the service reaches straight past the
    decorator that is the thing under test."""
    return app.test_client()


@pytest.fixture()
def make_supplier(db_session):
    """Only ever used to prove a supplier is REFUSED, so this is
    deliberately the thinnest possible supplier: a user row with the
    role on it, and no profile. A supplier who cannot get past the
    decorator never reaches anything that would need one."""
    from src.domains.auth.models.user import User, UserRole, VerificationStatus

    def _make(email: str = "supplier@example.com"):
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash="x",
            role=UserRole.SUPPLIER,
            verification_status=VerificationStatus.VERIFIED,
        )
        db_session.add(user)
        db_session.commit()
        return user

    return _make


@pytest.fixture()
def make_business(db_session):
    from src.domains.auth.models.user import User, UserRole, VerificationStatus

    def _make(email: str, phone: str = "0821234567"):
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash="x",
            role=UserRole.BUSINESS,
            verification_status=VerificationStatus.VERIFIED,
            phone_number=phone,
        )
        db_session.add(user)
        db_session.commit()
        return user

    return _make
