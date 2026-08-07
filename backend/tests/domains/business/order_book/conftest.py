"""
Order Book test fixtures. Identical shape to loan_book/conftest.py --
uses the same real create_app("testing") factory, same
make_business_user (VERIFIED status, since fully_authenticated
re-checks this against the database on every request).

NOT YET RUN against a real database in this environment -- see the
handoff notes for why (no Postgres reachable from the sandbox this was
built in). Written to the exact same shape as loan_book's own tests,
which ARE confirmed passing against real Postgres per that feature's
README, so this should run the same way once pointed at
TEST_DATABASE_URL on your machine.
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
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    return db.session


@pytest.fixture()
def make_business_user(db_session):
    from src.domains.auth.models.user import User, UserRole, VerificationStatus

    def _make(email: str):
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash="x",
            role=UserRole.BUSINESS,
            verification_status=VerificationStatus.VERIFIED,
        )
        db_session.add(user)
        db_session.commit()
        return user

    return _make
