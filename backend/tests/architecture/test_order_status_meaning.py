"""
ARCHITECTURE BOUNDARY TEST -- "a real sale" is one definition.

THE FAILURE THIS PREVENTS, named by V2_14 before the code existed:

    "Sales totals, trust stats, repeat-business counts and
     performance_stats_for_supplier all currently read
     status == CONFIRMED and mean 'a real sale'. Once CONFIRMED can
     move to COMPLETED, every one of those is silently wrong... That
     migration of MEANING is the largest and least visible part of this
     work, and the part most likely to be missed."

There were seventeen of them. They now read TRADED_STATUSES.

WHY A TEST AND NOT A CODE REVIEW. This failure has no symptom. Nothing
raises, nothing 500s, no test goes red -- a supplier's sales figures
simply shrink as their orders succeed, and the better they do the more
wrong the number gets. Somebody would eventually notice their totals
were falling during a good month and have no idea why.

It is also the single easiest mistake to reintroduce: `status ==
CONFIRMED` is the obvious thing to type, it reads correctly in English,
and it is wrong.

WHAT IS STILL ALLOWED, and each is a genuine exception:

    approve_order   WRITES CONFIRMED. Setting a status is not reading
                    one, and this is the moment the status is created.
    cancel_order    GUARDS on CONFIRMED specifically -- whether a
                    DISPATCHED order may still be cancelled is V2_14's
                    open question 4, and answering it by widening a
                    comparison would be deciding it by accident.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator, List

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = BACKEND_ROOT / "src"
MODEL = SRC_ROOT / "domains" / "network" / "orders" / "models" / "stock_order.py"

#: (file, function) pairs that may name CONFIRMED directly.
ALLOWED = {
    ("order_management_service.py", "approve_order"),
    ("order_management_service.py", "cancel_order"),
    # THE STATE MACHINE ITSELF. fulfilment_service names CONFIRMED as
    # the SOURCE of a transition -- "which statuses may become
    # DISPATCHED" -- which is a different question from "did this
    # sell", and the only place the first question is answered.
    #
    # Widening these to TRADED_STATUSES would be a real bug in the
    # other direction: it would let a COMPLETED order be marked
    # dispatched, which is stock leaving after it already arrived.
    ("fulfilment_service.py", "<module>"),
    ("fulfilment_service.py", "mark_dispatched"),
}


def _python_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        yield path


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))


def _enclosing(tree: ast.Module, line: int) -> str:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.lineno <= line <= (node.end_lineno or node.lineno):
                return node.name
    return "<module>"


def _confirmed_mentions(tree: ast.Module) -> List[int]:
    """Lines naming StockOrderStatus.CONFIRMED."""
    lines = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "CONFIRMED"
            and isinstance(node.value, ast.Name)
            and node.value.id == "StockOrderStatus"
        ):
            lines.append(node.lineno)
    return lines


def test_a_real_sale_has_one_definition() -> None:
    """Every "has this actually sold" query reads TRADED_STATUSES.

    If this fails, somebody's sales figures are about to start
    shrinking as their orders succeed.
    """
    offenders = []

    for path in _python_files(SRC_ROOT):
        if path == MODEL:
            # The model DEFINES the statuses and the groups. It is the
            # one place the name belongs.
            continue

        tree = _parse(path)
        for line in _confirmed_mentions(tree):
            where = (path.name, _enclosing(tree, line))
            if where in ALLOWED:
                continue
            offenders.append(f"{path.relative_to(BACKEND_ROOT)}:{line} in {where[1]}()")

    assert not offenders, (
        "These read StockOrderStatus.CONFIRMED directly. If the question is "
        '"did this actually sell", the answer is TRADED_STATUSES -- an order '
        "that completed successfully is still a sale:\n  " + "\n  ".join(sorted(offenders))
    )


def test_the_status_groups_stay_coherent() -> None:
    """The three groups are not independent opinions.

    A status that is both traded and terminal is fine (COMPLETED is
    both). A status that is open and terminal at once is a
    contradiction, and would make "how many orders are outstanding"
    unanswerable.
    """
    from src.domains.network.orders.models.stock_order import (
        OPEN_STATUSES,
        TERMINAL_STATUSES,
        TRADED_STATUSES,
        StockOrderStatus,
    )

    assert not (set(OPEN_STATUSES) & set(TERMINAL_STATUSES)), (
        "a status cannot be both open and finished"
    )
    assert set(OPEN_STATUSES) <= set(TRADED_STATUSES), (
        "an open order is one that sold and has not finished -- if a status "
        "is open but not traded, one of the two groups is wrong"
    )
    assert StockOrderStatus.COMPLETED in TERMINAL_STATUSES
    assert StockOrderStatus.COMPLETED in TRADED_STATUSES
    assert StockOrderStatus.CART not in TRADED_STATUSES, (
        "a cart is not a sale, however full it is"
    )
