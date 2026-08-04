"""
Shared pytest fixtures for the whole backend test suite.

`app` and `client` are promoted, unchanged in behaviour, from the
pattern already proven working in tests/test_auth.py -- not reinvented.
test_auth.py's own local copies still take priority for that file
specifically (pytest resolves same-named fixtures defined directly in a
test file before falling back to conftest.py), so nothing there changes;
every OTHER test file that had no local `app` fixture now gets one from
here.

`db_session` and `make_user` are new -- test_auth.py never needed them
(it drives everything through `client`, the HTTP layer), but the job- and
repository-level tests need direct database access without going through
a Flask route.
"""
from __future__ import annotations

import pytest

from src import create_app
from src.extensions import db
from src.shared.cache.cache import cache
from src.shared.email.email import get_fake_provider


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        get_fake_provider().clear()
        cache.clear()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """Direct database access for tests that don't go through the HTTP
    layer (job/repository tests). `app`'s own fixture already holds an
    active app_context() for the duration of the test, and already
    handles create_all()/drop_all() -- this just hands back the session
    living inside that context."""
    return db.session


@pytest.fixture()
def make_user():
    """
    Factory for building a User row with sensible defaults, overridable
    per test. Required, no-default columns (email, password_hash, role)
    always get a value even if the caller doesn't pass one; everything
    else follows the model's own defaults unless overridden.

    ASSUMPTION, not yet verified against base_model.py: BaseModel's
    created_at uses a Python-side `default=`, not `server_default=`,
    which is what makes `make_user(created_at=...)` actually take effect
    rather than being silently overwritten by the database at INSERT
    time. Standard SQLAlchemy behaviour, but flagging it since I haven't
    seen that file directly.

    Adds to db.session but does NOT commit -- tests call
    db_session.commit() themselves, matching
    test_cleanup_unverified_emails.py's own pattern.
    """
    from src.domains.auth.models.user import User, UserRole
    from src.shared.security.security import hash_password

    created = []

    def _make(
        email: str,
        *,
        password: str = "Abcd1234!",
        role: UserRole = UserRole.BUSINESS,
        **overrides,
    ):
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            **overrides,
        )
        db.session.add(user)
        created.append(user)
        return user

    return _make