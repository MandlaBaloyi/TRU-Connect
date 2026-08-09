"""Business Profile test fixtures. Identical shape to order_book's own
conftest.py -- same real create_app("testing") factory, same
make_business_user (VERIFIED status, since fully_authenticated
re-checks this against the database on every request)."""
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
