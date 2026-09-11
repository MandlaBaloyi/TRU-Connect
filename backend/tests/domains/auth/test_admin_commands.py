"""
The terminal gate: who may create staff, and who may change the
catalogue.

WHY THIS IS TESTED AT ALL, given that the module's own docstring calls
the prompt "a signature, not a wall". The honesty of that framing is
about the THREAT MODEL -- anyone who can run these already holds the
database password and could bypass the whole file with one UPDATE. It
is not permission for the check to be broken. The legitimate path has
to be attributable and has to refuse the wrong account, or the
attribution it records is fiction.

THE ONE THAT MATTERS MOST is test_bootstrap_closes_behind_itself.
`flask admin create` has exactly one unauthenticated path, justified
by there being nobody to authenticate against yet. If that path stayed
open after the first admin existed, it would be a self-service route
to a role that can reshape the shared catalogue -- the precise hole
the role was designed to avoid.
"""
from __future__ import annotations

import click
import pytest

from src.cli.commands.admin import ENV_ADMIN_EMAIL, ENV_ADMIN_PASSWORD
from src.domains.auth.models.user import AccountStatus, UserRole, VerificationStatus

PASSWORD = "Str0ng!Passw0rd"


@pytest.fixture()
def make_admin(make_user, db_session):
    def _make(email="staff@truconnect.co.za", **overrides):
        user = make_user(
            email,
            role=UserRole.ADMIN,
            verification_status=VerificationStatus.VERIFIED,
            password=PASSWORD,
            **overrides,
        )
        db_session.commit()
        return user

    return _make


@pytest.fixture(autouse=True)
def no_ambient_admin_env(monkeypatch):
    """The developer's real .env is loaded by the test runner to find
    the database, so APPLICATION_ADMIN_* would leak in and let a seed
    test pass for the wrong reason -- or fail one that should pass.
    Each test that needs them sets them explicitly.
    """
    monkeypatch.delenv(ENV_ADMIN_EMAIL, raising=False)
    monkeypatch.delenv(ENV_ADMIN_PASSWORD, raising=False)


def _seed_fn():
    """The seed command's own function, unwrapped.

    AppGroup.command wraps every callback in Flask's with_appcontext,
    which reads the ScriptInfo off a live click context and pushes its
    OWN app context. Neither exists here, and we would not want the
    second one if it did -- it would build a different app and leave
    these assertions querying a session the command never wrote to.
    __wrapped__ is the undecorated function, which runs inside the
    app context the fixtures already set up.
    """
    from src.cli.commands.admin import seed_admin

    return seed_admin.callback.__wrapped__()


def _answer(monkeypatch, *responses):
    """Feed click.prompt a queue of answers, in order."""
    queue = list(responses)

    def _prompt(*args, **kwargs):
        return queue.pop(0)

    monkeypatch.setattr(click, "prompt", _prompt)


class TestRequireAdmin:
    def test_an_admin_with_the_right_password_is_let_through(self, app, make_admin, monkeypatch):
        from src.cli._shared.authorise import require_admin

        admin = make_admin()
        _answer(monkeypatch, admin.email, PASSWORD)

        user_id, email = require_admin()

        assert user_id == str(admin.id)
        assert email == admin.email

    def test_a_business_is_refused_even_with_the_right_password(self, app, make_user, db_session, monkeypatch):
        """THE POINT OF THE WHOLE CHANGE. This used to be answered by an
        env allowlist of emails, which could drift from the permission
        system the rest of the app uses. Now it is the same role."""
        from src.cli._shared.authorise import require_admin

        user = make_user(
            "shop@example.com",
            role=UserRole.BUSINESS,
            verification_status=VerificationStatus.VERIFIED,
            password=PASSWORD,
        )
        db_session.commit()
        _answer(monkeypatch, user.email, PASSWORD)

        with pytest.raises(click.ClickException, match="not an admin"):
            require_admin()

    def test_a_wrong_password_never_reveals_that_the_account_is_staff(self, app, make_admin, monkeypatch):
        """The order of checks is the security property: password
        first, role second. Otherwise this prompt enumerates our staff
        for anyone who can guess an email."""
        from src.cli._shared.authorise import require_admin

        admin = make_admin()
        _answer(monkeypatch, admin.email, "wrong-password")

        with pytest.raises(click.ClickException) as exc:
            require_admin()
        assert "not valid" in str(exc.value)
        assert "admin" not in str(exc.value).lower()

    def test_an_unknown_email_fails_the_same_way_as_a_wrong_password(self, app, monkeypatch):
        from src.cli._shared.authorise import require_admin

        _answer(monkeypatch, "nobody@example.com", PASSWORD)

        with pytest.raises(click.ClickException, match="not valid"):
            require_admin()

    def test_a_deactivated_admin_is_refused(self, app, make_admin, monkeypatch):
        from src.cli._shared.authorise import require_admin

        admin = make_admin(account_status=AccountStatus.DEACTIVATED)
        _answer(monkeypatch, admin.email, PASSWORD)

        with pytest.raises(click.ClickException, match="not active"):
            require_admin()


class TestBootstrap:
    def test_bootstrap_closes_behind_itself(self, app, make_admin, db_session):
        """One admin existing is what flips `admin create` from the
        unauthenticated bootstrap path to the authorised one."""
        from src.cli.commands.admin import _existing_admins

        assert _existing_admins() == []

        make_admin()
        assert len(_existing_admins()) == 1

    def test_a_soft_deleted_admin_does_not_hold_the_door_shut(self, app, make_admin, db_session):
        """If a removed admin still counted, deleting the last one would
        leave a platform nobody can administer and no way back in."""
        from src.cli.commands.admin import _existing_admins

        admin = make_admin()
        admin.is_deleted = True
        db_session.commit()

        assert _existing_admins() == []


class TestSeedFromEnv:
    """`flask admin seed` -- the same bootstrap, read from .env."""

    def _seed(self, monkeypatch, email, password):
        monkeypatch.setenv(ENV_ADMIN_EMAIL, email)
        monkeypatch.setenv(ENV_ADMIN_PASSWORD, password)
        return _seed_fn()

    def test_it_creates_the_first_admin(self, app, db_session, monkeypatch):
        from src.domains.auth.repositories.user_repository import UserRepository

        self._seed(monkeypatch, "seeded@truconnect.co.za", PASSWORD)

        user = UserRepository.get_by_email("seeded@truconnect.co.za")
        assert user is not None
        assert user.role == UserRole.ADMIN
        assert user.account_status == AccountStatus.ACTIVE
        assert user.verification_status == VerificationStatus.VERIFIED

    def test_the_password_is_hashed_not_stored(self, app, db_session, monkeypatch):
        """THE WHOLE POINT OF SEEDING RATHER THAN AUTHENTICATING. The
        env variable is a one-time input; what persists is a bcrypt
        hash like any other account's, so the password can be changed
        and the variable cleared without the account breaking."""
        from src.domains.auth.repositories.user_repository import UserRepository
        from src.shared.security.security import verify_password

        self._seed(monkeypatch, "seeded@truconnect.co.za", PASSWORD)

        user = UserRepository.get_by_email("seeded@truconnect.co.za")
        assert PASSWORD not in user.password_hash
        assert verify_password(PASSWORD, user.password_hash)

    def test_it_is_idempotent(self, app, db_session, monkeypatch):
        """A deploy script may run it every time."""
        self._seed(monkeypatch, "seeded@truconnect.co.za", PASSWORD)
        self._seed(monkeypatch, "seeded@truconnect.co.za", PASSWORD)  # must not raise

        from src.cli.commands.admin import _existing_admins

        assert len(_existing_admins()) == 1

    def test_env_cannot_mint_a_second_admin(self, app, make_admin, db_session, monkeypatch):
        """THE BACK DOOR THIS CLOSES. If .env could create an admin at
        any time, it would be the self-service path to staff that the
        role is specifically designed not to have -- via a credential
        that ends up in CI logs and pasted into chat."""
        make_admin("first@truconnect.co.za")

        with pytest.raises(click.ClickException, match="may not mint another"):
            self._seed(monkeypatch, "second@truconnect.co.za", PASSWORD)

    def test_it_refuses_to_promote_a_trading_account(self, app, make_user, db_session, monkeypatch):
        """Silently turning a real shop into staff would be the worst
        possible outcome of a typo in .env."""
        make_user("shop@example.com", role=UserRole.BUSINESS, password=PASSWORD)
        db_session.commit()

        with pytest.raises(click.ClickException, match="Refusing to promote"):
            self._seed(monkeypatch, "shop@example.com", PASSWORD)

    def test_a_weak_password_is_refused(self, app, db_session, monkeypatch):
        with pytest.raises(click.ClickException, match="not strong enough"):
            self._seed(monkeypatch, "seeded@truconnect.co.za", "password")

    def test_missing_variables_say_which_ones(self, app, db_session, monkeypatch):
        with pytest.raises(click.ClickException, match=ENV_ADMIN_EMAIL):
            _seed_fn()


class TestCapabilities:
    """The seam: call sites ask for a JOB, not for a person.

    These tests exist to pin the seam's SHAPE, not today's answer.
    Today every active admin holds every capability, and that is the
    honest description of a one-person company. What must not rot is
    that the question being asked is "may you review the catalogue",
    so that the day it stops being admin-shaped, the change is one
    function and not an excavation.
    """

    def test_an_admin_holds_every_capability_today(self, app, make_admin, monkeypatch):
        from src.cli._shared.authorise import require_capability
        from src.cli._shared.capabilities import ALL

        admin = make_admin()
        for capability in ALL:
            _answer(monkeypatch, admin.email, PASSWORD)
            user_id, _ = require_capability(capability)
            assert user_id == str(admin.id), capability

    def test_a_business_holds_none_of_them(self, app, make_user, db_session, monkeypatch):
        from src.cli._shared.authorise import require_capability
        from src.cli._shared.capabilities import ALL

        user = make_user(
            "shop@example.com",
            role=UserRole.BUSINESS,
            verification_status=VerificationStatus.VERIFIED,
            password=PASSWORD,
        )
        db_session.commit()

        for capability in ALL:
            _answer(monkeypatch, user.email, PASSWORD)
            with pytest.raises(click.ClickException):
                require_capability(capability)

    def test_the_refusal_names_the_job_not_the_capability_string(
        self, app, make_user, db_session, monkeypatch
    ):
        """An error reading "you may not work the product match review
        queue" is actionable. One reading "missing catalogue:review" is
        a support ticket."""
        from src.cli._shared.authorise import require_capability
        from src.cli._shared.capabilities import ALL, CATALOGUE_REVIEW

        user = make_user("shop2@example.com", role=UserRole.BUSINESS, password=PASSWORD)
        db_session.commit()
        _answer(monkeypatch, user.email, PASSWORD)

        with pytest.raises(click.ClickException) as exc:
            require_capability(CATALOGUE_REVIEW)

        assert ALL[CATALOGUE_REVIEW] in str(exc.value)
        assert CATALOGUE_REVIEW not in str(exc.value)

    def test_every_capability_has_a_human_sentence(self):
        """A name with no description would produce exactly the
        unactionable error the test above forbids."""
        from src.cli._shared import capabilities

        declared = {
            value
            for name, value in vars(capabilities).items()
            if name.isupper() and name != "ALL" and isinstance(value, str)
        }
        assert declared == set(capabilities.ALL)
        assert all(capabilities.ALL.values())
