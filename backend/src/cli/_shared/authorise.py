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
One gate: the role.

WHAT CALL SITES ASK FOR IS A CAPABILITY, NOT A PERSON. Every command
goes through require_capability(...), naming the job it needs doing --
catalogue:review, supplier:verify -- and TODAY that resolves to "are
you an active admin", because today one admin does everything. The
names live in capabilities.py; see that module on why the seam is
worth having while the machinery behind it is not.

The practical consequence: when a second staff role arrives, the
change is inside _has_capability below. No command file is touched,
and nothing has to be excavated to work out what it assumed.
"""
from __future__ import annotations

from typing import Optional, Tuple

import click


def _has_capability(user, capability: Optional[str]) -> bool:
    """Does this account hold this capability?

    THE ONE FUNCTION THAT CHANGES when staff stop being a single
    undivided role. Today every active admin holds every capability,
    which is the honest description of a one-person company: there is
    nobody to withhold anything from, and a grants table would be a
    join with one row per name and no second subject to distinguish.

    When that changes -- a finance admin who must not teach product
    aliases, a support agent who may verify suppliers but not mint
    staff -- the grant lookup goes HERE, and every call site already
    recorded which capability it wanted.

    `capability=None` means "be staff at all", which is what
    `admin create` genuinely needs.
    """
    from src.domains.auth.models.user import UserRole

    return user.role == UserRole.ADMIN


def require_capability(capability: str) -> Tuple[Optional[str], str]:
    """Prompt for credentials, check this capability, return
    (user_id, email) -- or abort.

    THE ENTRY POINT EVERY PRIVILEGED COMMAND SHOULD USE. Ask for what
    needs doing, not for who you believe may do it.
    """
    from src.cli._shared.capabilities import ALL

    return require_admin(purpose=ALL.get(capability, capability), capability=capability)


def require_admin(purpose: str = "do this", capability: Optional[str] = None) -> Tuple[Optional[str], str]:
    """Prompt for credentials and return (user_id, email), or abort.

    Prefer require_capability() above -- this is the check underneath
    it, called directly only by `admin create`, whose requirement
    really is "be staff" rather than any narrower job.

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

    # "YOUR ADMIN EMAIL", NOT "EMAIL". Every caller has just printed a
    # screen naming the SUBJECT of the action -- the supplier being
    # approved, the review being accepted -- so a bare "Email:" reads
    # as asking for that one again. This prompt wants the person
    # DECIDING, and the label has to say so.
    email = click.prompt("  Your admin email").strip().lower()
    password = click.prompt("  Your password", hide_input=True)

    user = UserRepository.get_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise click.ClickException("Those credentials are not valid.")
    if not _has_capability(user, capability):
        # TWO PHRASINGS, because they answer different questions. Asked
        # for a capability, the useful sentence names the JOB refused
        # ("may not work the product match review queue"). Asked only
        # to be staff, it names the ROLE -- saying "may not do this"
        # there would be true and useless.
        reason = (
            f"{email} may not {purpose}."
            if capability
            else f"{email} is not an admin account, so it may not {purpose}."
        )
        raise click.ClickException(reason + "\n  An admin is made with:  flask admin create")
    # CHECKED AFTER the capability, deliberately. "Your account is
    # suspended" is useful to learn only once it is established that
    # the account was the right one to be asking about.
    if user.account_status != AccountStatus.ACTIVE:
        raise click.ClickException("That account is not active.")

    click.echo(f"  Signed in as {email}\n")
    return str(user.id), email


