"""
ARCHITECTURE BOUNDARY TESTS -- the Finance Engine's isolation, enforced.

WHY THIS FILE EXISTS:
"Finance must never know about domains" is a rule. Rules decay. Someone
rushing a feature writes

    from src.domains.business.loan_book.repositories import LoanRepository

inside Finance. Review misses it. Six months later Finance depends on
Loan Book while Loan Book depends on Finance, circular imports begin,
and untangling it is a project rather than a fix.

This test makes that impossible instead of merely discouraged: it parses
every file under shared/finance/ with Python's own AST module (not a
text search -- a regex would miss aliased or multi-line imports and
would false-positive on the word appearing in a docstring) and fails if
any forbidden import appears.

Same discipline as master_scheduler's test_registry_defines_no_jobs_itself:
verify the STRUCTURE, not just the behaviour.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator, List, Tuple

import pytest

FINANCE_ROOT = Path(__file__).resolve().parents[2] / "src" / "shared" / "finance"

# Finance may import ONLY these. Anything else in the project is a
# violation -- Finance is a leaf: things depend on it, it depends on
# almost nothing.
ALLOWED_INTERNAL_PREFIXES = (
    "src.shared.finance",
    "src.shared.constants",
    "src.core",
)

# Named explicitly (rather than relying on the allow-list alone) so the
# failure message can say WHICH boundary was crossed and why it matters.
FORBIDDEN_PREFIXES = {
    "src.domains": (
        "Finance must never depend on a business domain. Domains use "
        "Finance, never the reverse -- otherwise the dependency becomes "
        "circular and neither can be understood or tested alone."
    ),
    "src.shared.audit": (
        "Auditing is a separate platform engine. Finance CALCULATES; the "
        "domain calling it decides what to audit. Finance emitting its "
        "own audit events would make every calculation a side-effecting "
        "operation."
    ),
    "src.shared.security": (
        "Authentication/permissions belong to the domains and the "
        "security engine. Finance has no idea who is calling it, by "
        "design -- it might be an HTTP request, a scheduled job, or a test."
    ),
    "src.shared.queue": (
        "Background execution is a platform concern. A calculation that "
        "silently enqueues work is not a calculation."
    ),
    "src.shared.email": "Notifications are not a finance concern.",
    "src.shared.monitoring": "Monitoring is a separate platform engine.",
    "src.shared.cache": "Caching is a platform concern, not a finance one.",
}


def _finance_files() -> List[Path]:
    if not FINANCE_ROOT.exists():
        pytest.skip(f"Finance engine not found at {FINANCE_ROOT}")
    return sorted(FINANCE_ROOT.rglob("*.py"))


def _imports_in(path: Path) -> Iterator[Tuple[str, int]]:
    """Every module name imported by `path`, with its line number.

    Uses the AST rather than text matching so that `import x as y`,
    multi-line imports, and conditional imports inside functions are all
    caught, while the same words appearing in a docstring are not."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                yield node.module, node.lineno


def test_finance_never_imports_forbidden_modules():
    violations = []
    for path in _finance_files():
        for module, lineno in _imports_in(path):
            for forbidden, reason in FORBIDDEN_PREFIXES.items():
                if module == forbidden or module.startswith(forbidden + "."):
                    rel = path.relative_to(FINANCE_ROOT.parents[2])
                    violations.append(f"\n  {rel}:{lineno}\n    imports {module}\n    -> {reason}")

    assert not violations, (
        "ARCHITECTURE VIOLATION -- the Finance Engine imported something it "
        "must never depend on:" + "".join(violations) + "\n\n"
        "Finance is a leaf module: domains depend on IT, never the reverse. "
        "If you need this behaviour, it belongs in the calling domain, not here."
    )


def test_finance_only_imports_from_its_own_allowed_surface():
    """
    Stricter companion to the test above: rather than only banning a
    known list, this asserts Finance imports NOTHING internal beyond its
    explicitly allowed surface -- so a brand-new shared module added
    next year is excluded by default rather than needing to be
    remembered and added to the forbidden list.
    """
    violations = []
    for path in _finance_files():
        for module, lineno in _imports_in(path):
            if not module.startswith("src."):
                continue  # stdlib / third-party handled separately
            if not module.startswith(ALLOWED_INTERNAL_PREFIXES):
                rel = path.relative_to(FINANCE_ROOT.parents[2])
                violations.append(f"\n  {rel}:{lineno} imports {module}")

    assert not violations, (
        "ARCHITECTURE VIOLATION -- Finance imported an internal module outside "
        "its allowed surface:" + "".join(violations) + f"\n\n"
        f"Finance may only import from: {', '.join(ALLOWED_INTERNAL_PREFIXES)}.\n"
        "Anything else means logic is leaking into the engine that belongs "
        "in a domain or another platform engine."
    )


def test_finance_does_not_import_flask():
    """
    Finance must be callable from an HTTP request, a scheduled job, a
    CLI, or a test with equal ease. Importing Flask would silently tie
    every calculation to a web request lifecycle -- exactly the coupling
    that caused the audit service's app-context bug.
    """
    violations = []
    for path in _finance_files():
        for module, lineno in _imports_in(path):
            if module == "flask" or module.startswith("flask."):
                rel = path.relative_to(FINANCE_ROOT.parents[2])
                violations.append(f"\n  {rel}:{lineno} imports {module}")

    assert not violations, (
        "ARCHITECTURE VIOLATION -- Finance imported Flask:" + "".join(violations) + "\n\n"
        "The engine must work identically inside a request, a scheduled job, "
        "or a plain test. Web concerns belong to the domain's API layer."
    )


def test_finance_does_not_import_sqlalchemy():
    """
    Finance calculates money; it never persists it. Storage belongs to
    each domain's own repositories, which is what lets a domain choose
    its own table shape while still using identical money maths.
    """
    violations = []
    for path in _finance_files():
        for module, lineno in _imports_in(path):
            if module.startswith(("sqlalchemy", "flask_sqlalchemy")):
                rel = path.relative_to(FINANCE_ROOT.parents[2])
                violations.append(f"\n  {rel}:{lineno} imports {module}")

    assert not violations, (
        "ARCHITECTURE VIOLATION -- Finance imported a database library:"
        + "".join(violations)
        + "\n\nFinance calculates; domains persist."
    )


def test_finance_never_uses_float_for_money():
    """
    Scans for `float(` calls in the engine. Money must never touch a
    float -- 0.1 + 0.2 != 0.3, and those errors compound silently until
    a shop owner's total is a cent off, which destroys trust in every
    other figure the app shows.

    Deliberately allows the word "float" in comments and docstrings
    (where it's discussed constantly, precisely because it's banned) by
    checking the AST for real calls rather than searching text.
    """
    violations = []
    for path in _finance_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "float"
            ):
                rel = path.relative_to(FINANCE_ROOT.parents[2])
                violations.append(f"\n  {rel}:{node.lineno} calls float()")

    assert not violations, (
        "ARCHITECTURE VIOLATION -- Finance called float():" + "".join(violations) + "\n\n"
        "Money is integer minor units, always. Use Decimal for intermediate "
        "exact arithmetic; see core/money.py."
    )
