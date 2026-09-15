"""
ARCHITECTURE BOUNDARY TEST -- money may not reach the ranking.

THE RULE THIS DEFENDS (V2_16):

    A supplier's plan buys REACH. It does not buy a place in what a
    shop has EARNED, and it never buys which offer they are shown for
    a product they already want.

WHY IT NEEDS A TEST AND NOT A CODE REVIEW. This is the boundary most
likely to be argued away later, and by somebody with a good reason: a
paying supplier will eventually ask why their offer does not win, and
the change that grants it is one line in a sort key. The damage is not
visible in a diff -- the feed keeps working, the tests keep passing,
and the only symptom is that shopkeepers slowly stop trusting a rail
they cannot prove is bought.

THREE RULES:

  1. NOTHING UNDER demand/ READS A PLAN OR A KIND. The demand engine
     answers "what does this shop need" and must not be able to see who
     is paying. test_demand_independence.py already forbids importing
     the supplier domain at all; this is the narrower, more specific
     statement, so a future refactor that moves the enum somewhere
     "neutral" does not quietly open the door.

  2. offer_selection NEVER READS A PLAN. Which supplier's offer a shop
     sees for a product they already want is a RELATIONSHIP and PRICE
     decision (its own docstring: "lead with price and TruConnect
     becomes a price comparison site; lead with relationship and it is
     loyal but possibly expensive"). If that becomes purchasable the
     price comparison is a lie, and the catalogue -- the most expensive
     thing this platform owns -- stops meaning anything. V2_16 Part 7
     item 7, named there as the one most likely to be argued for.

  3. buy_it_again IS NEVER TIER-CAPPED. It is the shop's own confirmed
     purchase history. A per-supplier ceiling there would hide a shop's
     own stock from itself in the name of an anti-domination rule that
     does not apply to a rail which only remembers.

Parsed with the AST rather than grepped, same discipline as the curtain
and demand-independence tests: a regex would false-positive on the long
comments this codebase is full of, and would miss an aliased import.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator, List

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = BACKEND_ROOT / "src"
DEMAND_ROOT = SRC_ROOT / "domains" / "business" / "demand"
OFFER_SELECTION = SRC_ROOT / "domains" / "catalogue" / "discovery" / "services" / "offer_selection.py"
SECTIONS = SRC_ROOT / "domains" / "network" / "community" / "business" / "sections.py"

#: The names that mean "this supplier pays us". Any of them appearing
#: where the rules above forbid is the violation, however it got there.
PAID_NAMES = {
    "plan_tier",
    "plan_expires_at",
    "SupplierPlanTier",
    "supplier_kind",
    "SupplierKind",
}


def _python_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        yield path


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))


def _paid_names_used(tree: ast.Module) -> List[str]:
    """Every mention of a plan/kind name, as an attribute, a bare name,
    a keyword argument or an imported symbol."""
    found: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in PAID_NAMES:
            found.append(node.attr)
        elif isinstance(node, ast.Name) and node.id in PAID_NAMES:
            found.append(node.id)
        elif isinstance(node, ast.keyword) and node.arg in PAID_NAMES:
            found.append(node.arg)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in PAID_NAMES:
                    found.append(alias.name)
    return found


def test_the_demand_engine_cannot_see_who_is_paying() -> None:
    """THE INVARIANT THE WHOLE ANTI-DOMINATION PROPERTY RESTS ON.

    A feed where spend moves organic results is an auction wearing a
    recommendation's clothes.
    """
    offenders = []
    for path in _python_files(DEMAND_ROOT):
        used = _paid_names_used(_parse(path))
        if used:
            offenders.append(f"{path.relative_to(BACKEND_ROOT)} -> {sorted(set(used))}")

    assert not offenders, (
        "The demand engine must not read a supplier's plan or kind:\n  "
        + "\n  ".join(sorted(offenders))
    )


def test_offer_selection_cannot_be_bought() -> None:
    """V2_16 PART 7, ITEM 7 -- the one most likely to be argued for.

    If a plan can decide whose offer a shop sees, "also from 3
    suppliers" and every price comparison built on it become claims
    nobody should believe.
    """
    used = _paid_names_used(_parse(OFFER_SELECTION))

    assert not used, (
        "offer_selection must choose on stock, relationship and price "
        f"alone -- found {sorted(set(used))}. Which supplier a shop is "
        "shown for a product they already want is not for sale."
    )


def test_buy_it_again_is_never_capped_per_supplier() -> None:
    """A shop's own purchase history is not a recommendation, so the
    anti-domination ceiling does not apply to it. Capping it would hide
    a shop's own stock from itself."""
    tree = _parse(SECTIONS)

    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "buy_it_again":
            target = node
            break

    assert target is not None, "buy_it_again has moved -- this test needs updating"

    calls = [
        n.func.id
        for n in ast.walk(target)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    ]
    assert "_cap_per_supplier" not in calls, (
        "buy_it_again must not apply the per-supplier ceiling: it is the "
        "shop's own confirmed orders, and a wholesaler appearing often "
        "there is a fact about their trading rather than domination."
    )
