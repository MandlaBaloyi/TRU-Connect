"""
ARCHITECTURE BOUNDARY TEST -- the verification curtain, enforced.

THE RULE THIS DEFENDS (V2_03 Part 4.5, V2_12 Phase 1):

  An unverified supplier is invisible to buyers. Not findable in
  search, no storefront, cannot be ordered from.

WHY IT NEEDS A TEST AND NOT A CODE REVIEW. The rule is enforced in the
repository layer for exactly one reason, stated in V2_03 itself:

  "A visibility rule applied per-endpoint is a rule that leaks the
   first time somebody adds an endpoint."

A future feature that wants a supplier -- a recommendation panel, a
"suppliers near you" map, a shared basket -- will reach for
SupplierProfileRepository.get_by_id() because that is the obvious name,
and it will work perfectly in testing. It will also silently show
unverified suppliers to buyers, and nobody will notice until one of
them takes an order. This test is what turns that from a mistake
somebody has to catch into a build failure.

TWO RULES:

  1. Business-facing code (src/domains/network/) must reach suppliers
     through get_visible_by_id, not get_by_id -- EXCEPT on the
     existing-record paths listed below, where the curtain would
     rewrite history rather than stop future trade.

  2. Nothing outside src/domains/verification/ may compare
     verification_status by hand. One definition of "visible", in one
     module, or the rule stops being one rule.

Parsed with Python's AST rather than grepped, same discipline as
test_ai_boundaries.py: a regex would false-positive on the words
appearing in the long comments this codebase is full of, and would miss
an aliased import.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator, List, Tuple

BACKEND_ROOT = Path(__file__).resolve().parents[2]
NETWORK_ROOT = BACKEND_ROOT / "src" / "domains" / "network"
DOMAINS_ROOT = BACKEND_ROOT / "src" / "domains"
VERIFICATION_ROOT = DOMAINS_ROOT / "verification"

#: The ungated lookup. Correct for a supplier reading their own shop,
#: wrong for a buyer reading somebody else's.
UNGATED = "get_by_id"
GATED = "get_visible_by_id"
REPOSITORY = "SupplierProfileRepository"

#: Business-facing files permitted to use the UNGATED lookup, each with
#: the reason it is not a leak.
#:
#: THE PRINCIPLE, and it is worth stating because the list will grow:
#: the curtain covers DISCOVERY and NEW COMMERCE. It does not cover
#: EXISTING RECORDS. A supplier whose verification is revoked really
#: did sell those goods last month, and erasing them from a business's
#: own order history would make that history lie. Revocation stops
#: future trade; it does not rewrite the past.
EXISTING_RECORD_PATHS = {
    # An established connection is a relationship that already exists.
    "connections/services/connection_list_service.py",
    # Reporting a supplier must stay possible -- especially one who was
    # hidden BECAUSE something was wrong with them.
    "connections/services/report_service.py",
    # Requests already sent, and the supplier's own side of them. Only
    # request_connection (creating a NEW one) is gated.
    "connections/services/request_service.py",
    # Cancelling an order that was placed while the supplier was live.
    "orders/services/cancellation_service.py",
    # Viewing, emptying and removing FROM a cart stay possible; adding
    # to one does not. A business must be able to see and clear a cart
    # that has become unorderable, rather than find it silently gone.
    "orders/services/cart_service.py",
    # Past orders. The clearest case of all.
    "orders/services/order_history_service.py",
    # Finishing an order that was placed while the supplier was live.
    # The lookup here is a SUPPLIER fetching their OWN profile to stamp
    # themselves on a dispatch event -- the curtain applied there would
    # hide a supplier from themselves, which is the one thing
    # visibility.py says it must never do.
    "orders/services/fulfilment_service.py",
}


def _python_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        yield path


def _attribute_calls(tree: ast.AST) -> Iterator[Tuple[str, str, int]]:
    """Yield (object_name, attribute_name, lineno) for every `X.y(...)`."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            yield func.value.id, func.attr, node.lineno


def test_business_facing_code_uses_the_gated_lookup() -> None:
    """RULE 1. Anything in network/ that reaches a supplier profile goes
    through the curtain, unless it is on an existing-record path."""
    offenders: List[str] = []

    for path in _python_files(NETWORK_ROOT):
        relative = path.relative_to(NETWORK_ROOT).as_posix()
        if relative in EXISTING_RECORD_PATHS:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for obj, attr, lineno in _attribute_calls(tree):
            if obj == REPOSITORY and attr == UNGATED:
                offenders.append(f"{relative}:{lineno}")

    assert not offenders, (
        "Business-facing code reached a supplier through the UNGATED lookup, "
        "which shows unverified suppliers to buyers:\n  "
        + "\n  ".join(offenders)
        + f"\n\nUse {REPOSITORY}.{GATED}() instead. If this really is an "
        "existing-record path (order history, an established connection), add "
        "it to EXISTING_RECORD_PATHS in this file WITH the reason."
    )


def test_only_verification_decides_what_visible_means() -> None:
    """RULE 2. No hand-rolled SupplierVerificationStatus comparisons.

    A second definition of "visible" is worse than none: the two drift,
    and the drift is invisible until a supplier appears on one screen
    and not another. Reading the field to DISPLAY a badge is fine --
    that is the supplier_profile model's own to_dict. Comparing it to
    decide access is not.

    THE CHECK IS ON THE ENUM, NOT ON THE FIELD NAME, and the first
    draft of this test got that wrong -- it matched `verification_status`
    as an attribute and flagged seven innocent files. auth.users has
    its own verification_status, an ACCOUNT-level fact about whether
    somebody confirmed their email; SupplierProfile's is a COMMERCIAL
    trust judgement. supplier_profile.py's own docstring calls this out:
    "two different concepts that happen to share similar-looking
    states". Matching the name conflates exactly the two things that
    model deliberately keeps apart.
    """
    offenders: List[str] = []
    enum_name = "SupplierVerificationStatus"

    for path in _python_files(DOMAINS_ROOT):
        if VERIFICATION_ROOT in path.parents or path.parent == VERIFICATION_ROOT:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            for part in (node.left, *node.comparators):
                for inner in ast.walk(part):
                    if isinstance(inner, ast.Name) and inner.id == enum_name:
                        offenders.append(f"{path.relative_to(DOMAINS_ROOT).as_posix()}:{node.lineno}")

    assert not offenders, (
        f"{enum_name} was compared outside the verification domain:\n  "
        + "\n  ".join(sorted(set(offenders)))
        + "\n\nUse src.domains.verification.visibility.is_visible_to_buyers() "
        "or visible_filter(). One definition of visible, in one place."
    )


def test_the_visibility_rule_states_what_is_allowed_not_what_is_forbidden() -> None:
    """VISIBLE_STATUSES must be a whitelist.

    Not pedantry. If the rule were `!= UNVERIFIED`, then adding
    SUSPENDED or EXPIRED later would make every one of those suppliers
    instantly sellable, with no code change and no test failure. A
    whitelist fails the safe way: a new status is invisible until
    somebody decides otherwise.
    """
    from src.domains.supplier.supplier_profile.models.supplier_profile import (
        SupplierVerificationStatus,
    )
    from src.domains.verification.visibility import VISIBLE_STATUSES

    assert isinstance(VISIBLE_STATUSES, tuple)
    assert SupplierVerificationStatus.UNVERIFIED not in VISIBLE_STATUSES
    assert SupplierVerificationStatus.PENDING not in VISIBLE_STATUSES, (
        "PENDING means a decision is in progress, not that it succeeded."
    )
