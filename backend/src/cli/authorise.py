"""
Who is allowed to change the catalogue from a terminal.

THE HONEST FRAMING FIRST, because overselling this would be worse than
not having it. Anyone who can run `flask catalogue accept` already has
shell access to the server and the database credentials in .env. They
could bypass every line of this file with one UPDATE statement.



  ---------------------------------------------------------------------
  THIS PROMPT IS NOT A WALL. IT IS A SIGNATURE.
  ---------------------------------------------------------------------

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

  A REAL BOUNDARY. Shell access and permission to shape the shared
  catalogue are different things, and they stop being the same thing
  the moment anyone else can deploy.

THE GATE IS NOW A ROLE, and this is the change that made the rest of
this file honest. It used to read an env allowlist of emails, with a
docstring apologising that "UserRole has BUSINESS and SUPPLIER; admin
is a comment on the enum". That is no longer true: UserRole.ADMIN is
real, `flask admin create` mints one, and staff accounts are refused
by every marketplace endpoint (core.decorators.participants_only).
So the question "may you do this" is answered by the same permission
system the rest of the app uses, rather than by a list in a file that
could drift from it.

AND THE EMAIL ALLOWLIST IS GONE. There used to be a
CATALOGUE_REVIEWERS variable listing who could approve matches, from
back when there was no role to ask about. Keeping it as an optional
"narrowing" on top of the role was a second place for the answer to
live, and two sources of truth for one question is how a deployment
ends up with an admin who cannot do the job they were created for --
with the refusal blamed on the code rather than on a stale env var.
One gate: the role. Split catalogue duty off into its own permission
the day a finance admin actually exists, rather than pre-building the
distinction in a text file.
"""
from __future__ import annotations

from typing import Optional, Tuple

import click


def require_admin(purpose: str = "do this") -> Tuple[Optional[str], str]:
    """Prompt for credentials and return (user_id, email), or abort.

    Verified against the SAME password hash the app uses. There is no
    second credential to leak, no shared token in .env that outlives the
    person who knew it, and revoking someone is the ordinary act of
    deactivating their account or changing their role.

    THE ORDER OF CHECKS IS DELIBERATE: password first, then role, then
    status. Announcing "that account is not an admin" to someone who
    has not proved they own it would turn this prompt into a way to
    enumerate which of our users are staff.
    """
    from src.domains.auth.models.user import AccountStatus, UserRole
    from src.domains.auth.repositories.user_repository import UserRepository
    from src.shared.security.security import verify_password

    email = click.prompt("  Email").strip().lower()
    password = click.prompt("  Password", hide_input=True)

    user = UserRepository.get_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise click.ClickException("Those credentials are not valid.")
    if user.role != UserRole.ADMIN:
        raise click.ClickException(
            f"{email} is not an admin account, so it may not {purpose}.\n"
            "  An admin is made with:  flask admin create"
        )
    if user.account_status != AccountStatus.ACTIVE:
        raise click.ClickException("That account is not active.")

    click.echo(f"  Signed in as {email}\n")
    return str(user.id), email


def require_reviewer() -> Tuple[Optional[str], str]:
    """Catalogue review duty. Kept as its own name rather than calling
    require_admin everywhere, so that the day reviewing stops being an
    admin-only act, there is one function to change instead of every
    call site."""
    return require_admin(purpose="work the review queue")
