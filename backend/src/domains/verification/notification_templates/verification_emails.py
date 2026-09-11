"""
The wording of every verification email, decided in ONE place.

WHY A MODULE AND NOT JUST TEMPLATE FILES. The HTML holds the layout;
this holds the DECISIONS -- which rung of the reminder ladder says
what, when a contact address appears, and what a supplier is told
versus what we record about them. Those are product decisions, and
scattering them across three Jinja files would mean changing the tone
of the ladder in three places and getting it right in two.

THE INTERNAL REASON IS NEVER IN AN EMAIL. A verification decision
carries a reason written for US -- it may read "documents appear
altered" or "watching this account" -- and interpolating it would hand
an internal assessment to the person it is about. The reason lives in
the audit trail. The supplier gets a route to a human instead.

TONE, WHICH IS THE FEATURE (V2_03 Part 4.5). "Your shop is ready and
nobody can see it yet" is motivating; "you are not verified" is a
scolding to somebody who has just spent an hour building a catalogue,
and it is also less accurate -- their work is real, it is the
visibility that is pending.
"""
from __future__ import annotations

from datetime import datetime, timezone

#: Where a supplier writes when they want a person rather than a
#: template. Overridden from config so a deployment can point it at a
#: real inbox without a code change.
DEFAULT_SUPPORT_EMAIL = "support@truconnect.co.za"


def _support_email() -> str:
    from flask import current_app

    return current_app.config.get("SUPPORT_EMAIL", DEFAULT_SUPPORT_EMAIL)


def _greeting_name(user, profile) -> str:
    """Never blank. A bare "Hi," reads as a broken mail-merge, which is
    what a supplier notices before they read anything else."""
    return (getattr(user, "first_name", None) or getattr(profile, "business_name", None) or "there")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%d %B %Y")


def approved(user, profile) -> tuple[str, str, dict]:
    """(template, subject, context) for "your shop is live".

    THE MOMENT THE SUPPLIER HAS BEEN WAITING FOR, and until this
    existed the platform changed a database row and told them nothing
    -- they would have found out by chance, next time they opened
    Settings.
    """
    return (
        "supplier/verification_approved.html",
        f"{profile.business_name or 'Your shop'} is now live on TRU Connect",
        {
            "owner_name": _greeting_name(user, profile),
            "business_name": profile.business_name or "Your shop",
            "decided_on": _today(),
        },
    )


def hidden(user, profile) -> tuple[str, str, dict]:
    """(template, subject, context) for a revocation.

    SENT EVEN THOUGH IT IS UNWELCOME. A supplier whose shop goes dark
    with no explanation concludes the platform is broken and keeps
    building into a void. Being told is worse news and better
    treatment.
    """
    return (
        "supplier/verification_hidden.html",
        f"{profile.business_name or 'Your shop'} is not visible on TRU Connect",
        {
            "owner_name": _greeting_name(user, profile),
            "business_name": profile.business_name or "Your shop",
            "support_email": _support_email(),
            "decided_on": _today(),
        },
    )


#: The reminder ladder, by stage. THREE RUNGS AND THEN SILENCE -- a
#: platform that emails forever about its OWN pending decision is
#: nagging somebody about work they cannot do anything about.
#:
#: The tone shifts deliberately across the three. The first two are
#: encouraging and about THEM; the last one says plainly that the wait
#: is on US, because by day seven the likely problem is on our side and
#: pretending otherwise would be dishonest.
_LADDER = [
    {
        "headline": "Your shop is ready — buyers cannot see it yet.",
        "body": (
            "Everything you have set up is saved. The day your business is verified, "
            "your catalogue, prices and terms all become visible at once — so it is "
            "worth using this time to finish adding what you sell."
        ),
        "show_contact": False,
    },
    {
        "headline": "Still getting your shop ready for buyers.",
        "body": (
            "Your account is waiting on verification. Nothing is wrong on your side, "
            "and nothing you have built is affected — businesses simply cannot find "
            "you until it is done."
        ),
        "show_contact": False,
    },
    {
        "headline": "Your shop is still waiting on us.",
        "body": (
            "This has taken longer than it should. Your account is still pending "
            "verification, and that is on our side rather than yours. Everything you "
            "have built is safe and will go live the moment it is done."
        ),
        "show_contact": True,
    },
]

#: How many rungs. Reaching this stage means the ladder is finished.
LADDER_LENGTH = len(_LADDER)


def reminder(user, profile, stage: int) -> tuple[str, str, dict]:
    """(template, subject, context) for rung `stage` (0-indexed)."""
    rung = _LADDER[stage]
    return (
        "supplier/verification_reminder.html",
        f"{profile.business_name or 'Your shop'} — {rung['headline']}",
        {
            "owner_name": _greeting_name(user, profile),
            "headline": rung["headline"],
            "body": rung["body"],
            "show_contact": rung["show_contact"],
            "support_email": _support_email(),
        },
    )
