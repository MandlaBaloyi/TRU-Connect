"""
Who is allowed to change the catalogue from a terminal.

THE HONEST FRAMING FIRST, because overselling this would be worse than
not having it. Anyone who can run `flask catalogue accept` already has
shell access to the server and the database credentials in .env. They
could bypass every line of this file with one UPDATE statement.

  ─────────────────────────────────────────────────────────────────────
  THIS PROMPT IS NOT A WALL. IT IS A SIGNATURE.
  ─────────────────────────────────────────────────────────────────────

What it buys is three things a bare command does not:

  ATTRIBUTION. MatchReview.decided_by_user_id has existed since the
  model was written and the CLI's first version took it as a --user
  flag, which is worthless: nobody types their own UUID, and an
  unverified one is a claim rather than a record. Proving the password
  turns "someone accepted this" into "Mandla accepted this at 21:14".

  DELIBERATION. Typing a password is a half-second pause before an
  action that writes a GLOBAL alias -- one that answers the same text
  for every supplier on the platform, forever. That pause is worth
  having on the one command whose blast radius is everybody.

  A REAL ALLOWLIST. Shell access and permission to shape the shared
  catalogue are different things, and they stop being the same thing
  the moment anyone else can deploy.

WHY NOT A ROLE. UserRole has BUSINESS and SUPPLIER; admin is a comment
on the enum, "reserved for a future admin/financial-partner role", and
inventing it here would mean a migration and a half-built permission
system to gate one command. An env allowlist is honest about being
temporary and disappears the day the control centre has real roles.
"""
from __future__ import annotations

import os
from typing import Optional, Tuple

import click

#: Comma-separated emails permitted to work the review queue.
#:
#: EMPTY MEANS NOBODY, not everybody. A misconfigured deployment must
#: fail closed -- the alternative is that forgetting to set one
#: environment variable silently opens the catalogue to any shell.
ALLOWLIST_ENV = "CATALOGUE_REVIEWERS"


def _allowlist() -> list:
    raw = os.environ.get(ALLOWLIST_ENV, "")
    return [entry.strip().lower() for entry in raw.split(",") if entry.strip()]


def require_reviewer() -> Tuple[Optional[str], str]:
    """Prompt for credentials and return (user_id, email), or abort.

    Verified against the SAME password hash the app uses. There is no
    second credential to leak, no shared token in .env that outlives the
    person who knew it, and revoking someone is the ordinary act of
    deactivating their account.
    """
    from src.domains.auth.models.user import AccountStatus
    from src.domains.auth.repositories.user_repository import UserRepository
    from src.shared.security.security import verify_password

    allowed = _allowlist()
    if not allowed:
        raise click.ClickException(
            f"{ALLOWLIST_ENV} is not set, so nobody may work the review queue.\n"
            "  Set it in .env to the emails permitted, e.g.\n"
            f"    {ALLOWLIST_ENV}=you@truconnect.co.za"
        )

    email = click.prompt("  Reviewer email").strip().lower()
    if email not in allowed:
        # DELIBERATELY SAID PLAINLY. This is not a login form facing the
        # internet -- it is a terminal on our own server, and being coy
        # about which of the two things was wrong would only waste the
        # time of the person who mistyped their own address.
        raise click.ClickException(f"{email} is not in {ALLOWLIST_ENV}.")

    password = click.prompt("  Password", hide_input=True)

    user = UserRepository.get_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise click.ClickException("Those credentials are not valid.")
    if user.account_status != AccountStatus.ACTIVE:
        raise click.ClickException("That account is not active.")

    click.echo(f"  Signed in as {email}\n")
    return str(user.id), email
