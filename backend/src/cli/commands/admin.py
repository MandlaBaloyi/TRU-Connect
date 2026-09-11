"""
`flask admin ...` -- making and listing the accounts that operate the
platform, as opposed to trading on it.

WHY THIS EXISTS AT ALL. UserRole.ADMIN is deliberately unreachable from
every registration path: there is no sign-up form, no invite link, no
"upgrade my account" endpoint. A self-service route to a role that can
reshape the shared product catalogue would be a hole rather than a
feature. That leaves exactly one way to mint one, and this is it --
run by somebody who already holds the server's credentials.

THE BOOTSTRAP PROBLEM, AND HOW IT IS ANSWERED. Creating an admin
should require being an admin. That rule cannot hold for the FIRST
one, or the role could never come into existence. So the check is
conditional on there already being somebody to check against:

    no admins exist  ->  bootstrap: shell access IS the authorisation
    admins exist     ->  an existing admin must sign in first

This is the ordinary shape of the problem (it is why `sudo` has a
first user and why databases ship with a superuser), and the important
part is that the unauthenticated door CLOSES BY ITSELF the moment it
has been used once. Nobody has to remember to lock it.

WHAT AN ADMIN IS NOT. It is not a super-business. Staff are refused by
every marketplace endpoint (core.decorators.participants_only), so an
admin has no Loan Book, no Order Book, no shopfront and no
connections. Making one does not give somebody a better version of the
app; it gives them a different job.
"""
from __future__ import annotations

import os

import click
from flask.cli import AppGroup

from src.cli._shared import audit as cli_audit
from src.shared.audit.event_types import AdminAuditEvent

admin_cli = AppGroup("admin", help="Create and inspect platform staff accounts.")

#: Credentials for the FIRST admin, read by `flask admin seed`.
#:
#: SEEDING, NOT AUTHENTICATING -- the distinction this whole command
#: rests on. These are read exactly once, at creation, and the password
#: is bcrypt-hashed into the users table like any other. Nothing ever
#: signs in against these variables: that would make the password
#: unrotatable, make account_status meaningless (a deactivated admin
#: whose password sits in .env still works), and collapse attribution
#: from "Mandla approved this" to "whoever holds the .env file did".
ENV_ADMIN_EMAIL = "APPLICATION_ADMIN_EMAIL"
ENV_ADMIN_PASSWORD = "APPLICATION_ADMIN_PASSWORD"


def _existing_admins():
    from src.domains.auth.models.user import User, UserRole

    return (
        User.query.filter_by(role=UserRole.ADMIN, is_deleted=False)
        .order_by(User.created_at)
        .all()
    )


@admin_cli.command("list")
def list_admins() -> None:
    """Who currently operates this platform."""
    from src.domains.auth.models.user import AccountStatus

    admins = _existing_admins()
    click.echo("")
    if not admins:
        click.echo("  No admin accounts exist.")
        click.echo("  The next `flask admin create` will run in bootstrap mode.\n")
        return

    click.echo(f"  ADMINS ({len(admins)})\n")
    for user in admins:
        flag = "" if user.account_status == AccountStatus.ACTIVE else f"  [{user.account_status.value.upper()}]"
        name = (f"{user.first_name or ''} {user.last_name or ''}").strip() or "(no name)"
        click.echo(f"    {user.email:38} {name:24} created {user.created_at:%Y-%m-%d}{flag}")
    click.echo("")


@admin_cli.command("create")
@click.option("--email", prompt="  New admin email", help="The account's email address.")
@click.option("--first-name", prompt="  First name", help="For attribution in the review log.")
@click.option("--last-name", prompt="  Last name", default="", help="Optional.")
def create_admin(email: str, first_name: str, last_name: str) -> None:
    """Create a platform staff account."""
    from src.domains.auth.models.user import AccountStatus, User, UserRole, VerificationStatus
    from src.domains.auth.repositories.user_repository import UserRepository
    from src.shared.security.security import hash_password, validate_password_complexity

    email = email.strip().lower()
    if UserRepository.exists_by_email(email):
        raise click.ClickException(f"{email} already has an account on this platform.")

    # SOFT-DELETED ROWS STILL HOLD THE EMAIL, because the uniqueness is
    # a database constraint on the column and does not know about
    # is_deleted -- while UserRepository.exists_by_email, correctly for
    # every other caller, does not count them. Checked separately so
    # this fails with a sentence rather than an IntegrityError
    # traceback, on the one command somebody runs once, at the moment
    # they are least oriented.
    if User.query.filter_by(email=email).first() is not None:
        raise click.ClickException(
            f"{email} belongs to a deleted account and cannot be reused.\n"
            "  Use a different address, or purge that row first."
        )

    existing = _existing_admins()
    click.echo("")
    if existing:
        click.echo(f"  {len(existing)} admin account(s) already exist, so one of them must authorise this.\n")
        from src.cli._shared.authorise import require_admin

        _, authorised_by = require_admin(purpose="create other admins")
        click.echo(f"  Authorised by {authorised_by}.")
    else:
        # THE ONLY UNAUTHENTICATED PATH IN THIS FILE, and it is
        # self-closing: it is reachable exactly once, because after it
        # runs _existing_admins() is no longer empty.
        authorised_by = None
        click.echo("  BOOTSTRAP: no admin exists yet, so shell access is the authorisation.")
        click.echo("  This is the only time `admin create` will not ask you to sign in.\n")

    # ASKED LAST AND CONFIRMED, because a mistyped password on an
    # account with no self-service reset is a locked door -- there is
    # no "forgot password" email flow that returns an admin to you.
    password = click.prompt("  Password", hide_input=True, confirmation_prompt=True)
    problems = validate_password_complexity(password)
    if problems:
        raise click.ClickException("That password is not strong enough:\n  - " + "\n  - ".join(problems))

    click.confirm(f"\n  Create an ADMIN account for {email}?", abort=True)

    user = UserRepository.create(
        email=email,
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
        first_name=first_name.strip() or None,
        last_name=last_name.strip() or None,
        # VERIFIED AND ACTIVE IMMEDIATELY, unlike a registration. The
        # email OTP exists to prove a stranger owns the address they
        # typed; nobody is a stranger here -- whoever ran this command
        # already had the database password. Leaving it UNVERIFIED
        # would only mean the account could not use the very commands
        # it was created for (fully_authenticated re-checks both).
        verification_status=VerificationStatus.VERIFIED,
        account_status=AccountStatus.ACTIVE,
    )

    # THE MOST PRIVILEGED ACT IN THE SYSTEM, and until now it left no
    # trace outside shell history -- which is per-machine, per-user and
    # trivially cleared. `authorised_by` is None for the bootstrap,
    # which is itself the fact worth recording: that is the one admin
    # nobody approved.
    cli_audit.record(
        AdminAuditEvent.STAFF_ACCOUNT_CREATED,
        user_id=str(user.id),
        email=user.email,
        metadata={
            "authorised_by": authorised_by,
            "bootstrap": authorised_by is None,
            "existing_admins": len(existing),
        },
    )
    click.echo(f"\n  Created {user.email} as ADMIN ({user.id}).")
    click.echo("  They can now work the review queue:  flask catalogue reviews\n")


@admin_cli.command("seed")
def seed_admin() -> None:
    """Create the first admin from .env, without prompting.

    THE SAME BOOTSTRAP AS `admin create`, with the typing removed --
    for a deploy script, a fresh clone, or a machine where hidden
    input is awkward. It obeys the identical rule: it works only while
    NO admin exists. Once one does, this command refuses and sends you
    to `admin create`, which asks an existing admin to authorise the
    next one.

    That is what stops .env from becoming a permanent back door. A
    variable that could mint an admin at any time would be exactly the
    self-service path to staff that UserRole.ADMIN is designed not to
    have -- and it would do it with a credential that gets copied into
    CI logs, shared with contractors, and pasted into chat.

    IDEMPOTENT, so a deploy script may run it every time: if the seeded
    admin already exists it reports and changes nothing. It will NEVER
    promote an existing non-admin account, which would silently turn a
    real shop or supplier into staff.
    """
    from src.domains.auth.models.user import AccountStatus, User, UserRole, VerificationStatus
    from src.domains.auth.repositories.user_repository import UserRepository
    from src.shared.security.security import hash_password, validate_password_complexity

    email = os.environ.get(ENV_ADMIN_EMAIL, "").strip().lower()
    password = os.environ.get(ENV_ADMIN_PASSWORD, "")
    if not email or not password:
        raise click.ClickException(
            f"Set both {ENV_ADMIN_EMAIL} and {ENV_ADMIN_PASSWORD} in .env first."
        )

    click.echo("")
    existing = UserRepository.get_by_email(email)
    if existing is not None:
        if existing.role != UserRole.ADMIN:
            raise click.ClickException(
                f"{email} already exists as a {existing.role.value.upper()} account.\n"
                "  Refusing to promote it -- change "
                f"{ENV_ADMIN_EMAIL} to an address nobody is trading under."
            )
        click.echo(f"  {email} is already an admin. Nothing to do.\n")
        return

    # SAME DOOR, SAME LOCK as `admin create`. Checked AFTER the
    # already-seeded case above so re-running a deploy script stays
    # quiet rather than failing a pipeline that has changed nothing.
    already = _existing_admins()
    if already:
        raise click.ClickException(
            f"{len(already)} admin account(s) already exist, so .env may not mint another.\n"
            "  Use `flask admin create`, which asks an existing admin to authorise it."
        )

    if User.query.filter_by(email=email).first() is not None:
        raise click.ClickException(f"{email} belongs to a deleted account and cannot be reused.")

    problems = validate_password_complexity(password)
    if problems:
        raise click.ClickException(
            f"{ENV_ADMIN_PASSWORD} is not strong enough:\n  - " + "\n  - ".join(problems)
        )

    user = UserRepository.create(
        email=email,
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
        verification_status=VerificationStatus.VERIFIED,
        account_status=AccountStatus.ACTIVE,
    )
    # SEPARATE EVENT FROM `create`. Both mint an admin; "a person typed
    # this at a terminal" and "a deploy script read it from .env"
    # answer the who question differently, and flattening them would
    # lose that.
    cli_audit.record(
        AdminAuditEvent.STAFF_ACCOUNT_SEEDED,
        user_id=str(user.id),
        email=user.email,
        metadata={"bootstrap": True},
    )
    click.echo(f"  Seeded {user.email} as ADMIN ({user.id}).")
    click.echo(f"  {ENV_ADMIN_PASSWORD} is now only a copy -- the account's own hash is authoritative.")
    click.echo("  Change the password from the app, and clear that variable, once you are signed in.\n")
