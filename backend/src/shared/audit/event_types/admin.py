"""
Staff actions: creating the accounts that operate the platform, and
signing in at a terminal to use them.

WHY THESE ARE AUDITED AT ALL, when the person doing them already holds
the database password and could bypass every check. The same reason
the CLI asks for a password in the first place: the point is not to
STOP somebody with shell access, it is to make the legitimate path
ATTRIBUTABLE. "Who made this admin, and when" is a question asked
after something goes wrong, and shell history is not an answer --
it is per-machine, per-user, and trivially cleared.

DOMAIN IS SECURITY, NOT AUTH. These are not a person signing in to use
the product; they are the operation of the platform itself. Grouping
them with ordinary logins would bury four events a year under a
hundred thousand.

CLI_SIGN_IN_FAILED IS THE MOST VALUABLE LINE HERE, and the easiest to
forget. A successful staff action leaves other traces -- a changed
row, an email, a catalogue alias. A FAILED attempt at the privileged
door leaves none at all, and repeated failures are exactly the signal
worth having after an incident.
"""
from __future__ import annotations

import enum


class AdminAuditEvent(str, enum.Enum):
    STAFF_ACCOUNT_CREATED = "admin.staff_account_created"
    #: `flask admin seed` -- the same act, from .env rather than a
    #: prompt. Kept separate because "created by a person at a
    #: terminal" and "created by a deploy script" answer the "who"
    #: question differently.
    STAFF_ACCOUNT_SEEDED = "admin.staff_account_seeded"

    CLI_SIGN_IN_SUCCEEDED = "admin.cli_sign_in_succeeded"
    CLI_SIGN_IN_FAILED = "admin.cli_sign_in_failed"
    #: Credentials were right, but the account may not do the thing --
    #: a different fact from a bad password, and a more interesting one.
    CLI_CAPABILITY_DENIED = "admin.cli_capability_denied"
