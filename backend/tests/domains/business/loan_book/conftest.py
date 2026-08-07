"""
Loan Book test fixtures.

Uses create_app("testing") -- the SAME real app factory test_auth.py
already uses -- so this correctly reads TEST_DATABASE_URL and registers
every real blueprint (including loan_book_bp), rather than hand-rolling
a bare Flask app with placeholder credentials.

make_business_user creates users with verification_status=VERIFIED --
a real logged-in business owner is verified by definition, and
fully_authenticated re-checks this against the database on every
request (see test_auth.py's own docstring: "even if one somehow did,
@fully_authenticated re-checks the database, not the token"). An
unverified test user would be correctly rejected with 403, which is
exactly what happened before this fixture set the field explicitly.
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