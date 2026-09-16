"""
Has this shop given the engine enough to run on?

WHY THIS LIVES IN demand/ AND NOT IN business_profile/. The question
"which answers are mandatory" has exactly one correct source: the list
of columns the engine actually reads. Anywhere else it becomes a second
copy that drifts the first time somebody adds a signal -- and the way
it drifts is silent, because a setup flow that stops collecting a field
does not fail, it just produces shops the engine cannot serve.

So this reads DeclaredSignals rather than the model. Add a field to
declared.read and forget to add it here and the step simply reports
what it always did; add a step here for something declared.read does
not use and the test below catches it. The dependency also already runs
this way round -- declared.read imports the business_profile
repository, so the reverse import would be a cycle.

IT DESCRIBES, IT DOES NOT WRITE. Every answer is saved through the
existing business_profile PATCH routes, which is the rule Mandla's
flow depends on: a step answered during setup is the same edit as the
same field in My Business, with one service, one validation and one
write path. A setup flow with its own writer is a second way for the
same column to be set, and the two will disagree within a month.

WHAT IS DELIBERATELY NOT HERE:

  THE SKIP. Step three may be skipped once (V2_18 4.3), and that is a
  per-device deferral the app owns -- there is no "skipped" column and
  there should not be. The truth on the server is simply whether a
  location exists; "they said not now" is a fact about a phone, not
  about a business.

  BUSINESS NAME. It is mandatory at REGISTRATION now, not here, so
  asking again in step one would be asking a question whose answer we
  already hold. It is also identity rather than fuel -- the engine
  never reads it.

  ANY NOTION OF "GOOD ENOUGH". A step is complete or it is not. A
  percentage here would invite a threshold, and a threshold is a place
  to quietly lower the bar when completion rates disappoint.
"""
from __future__ import annotations

from typing import Dict, List

from src.domains.business.demand.signals import declared

#: The three steps, in the order a person can answer them, and the
#: DeclaredSignals fields each one is responsible for.
#:
#: ORDER IS NOT ARBITRARY. Step one is the only question whose answer
#: the shopkeeper can give without thinking -- they know what they buy.
#: Step two asks them to generalise about themselves, which is harder.
#: Step three needs a permission dialog or a map drag, which is the
#: most expensive thing to ask for and therefore last and skippable.
STEP_WHAT_YOU_BUY = "whatYouBuy"
STEP_HOW_YOU_BUY = "howYouBuy"
STEP_WHERE_YOU_ARE = "whereYouAre"

#: Which steps a shop must answer before the gate lets them past.
#:
#: STEP THREE IS ABSENT ON PURPOSE. It is skippable, so requiring it
#: here would make "required" and "gating" two different things in two
#: files. The app skips at most once; the server never pretends the
#: location exists.
REQUIRED_STEPS = (STEP_WHAT_YOU_BUY, STEP_HOW_YOU_BUY)

ALL_STEPS = (STEP_WHAT_YOU_BUY, STEP_HOW_YOU_BUY, STEP_WHERE_YOU_ARE)


def _completed(signals: declared.DeclaredSignals) -> Dict[str, bool]:
    """One boolean per step, each derived from the fields that step
    writes.

    ONLY ONE OF STEP ONE'S FOUR QUESTIONS GATES IT. The step also asks
    the business category, how the business is set up, and how long it
    has been trading -- none of which the engine reads. They are
    collected because Mandla asked for them ("it's not about what you
    want to fit in the engine, it's about taking data that would be
    useful later for us"), and they are OPTIONAL precisely because of
    that: a question the engine cannot act on must never stand between
    a shopkeeper and their dashboard.

    So this stays the list of what the ENGINE consumes, which is the
    reason the whole module lives in demand/ rather than next to the
    profile. A step gates on fuel, never on curiosity.
    """
    return {
        STEP_WHAT_YOU_BUY: bool(signals.categories),
        # BOTH, because they answer different questions and neither
        # substitutes: rhythm sets WHEN the feed should be pressing,
        # spend sets WHAT SIZE of basket it may show. A shop with one
        # and not the other gets half a model.
        STEP_HOW_YOU_BUY: bool(signals.restock_rhythm) and bool(signals.weekly_spend_band),
        STEP_WHERE_YOU_ARE: signals.has_location,
    }


def setup_state(business_id) -> dict:
    """What this shop still has to answer.

    A MISSING PROFILE IS NOT AN ERROR, matching declared.read: a
    business that has never opened My Business has simply answered
    nothing, and every step comes back False. That is the state a brand
    new account is in and the whole reason the gate exists.
    """
    signals = declared.read(business_id)
    steps = _completed(signals)

    missing: List[str] = [step for step in ALL_STEPS if not steps[step]]

    return {
        "steps": steps,
        # WHAT THE GATE READS. True once the two required steps are
        # answered, whatever happened to the third.
        "requiredComplete": all(steps[step] for step in REQUIRED_STEPS),
        # WHAT A "FINISH YOUR SETUP" PROMPT READS, later. Distinct from
        # requiredComplete precisely so a skipped location stays visible
        # as unfinished without ever blocking anybody.
        "isComplete": all(steps.values()),
        # THE FIRST THING STILL MISSING, so the app never has to decide
        # the order itself and the two cannot disagree about it.
        "nextStep": missing[0] if missing else None,
    }
