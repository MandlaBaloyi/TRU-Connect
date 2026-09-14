"""
ARCHITECTURE BOUNDARY TEST -- the two Community feeds stay apart.

THERE ARE TWO "For You" TABS AND THEY ARE NOT THE SAME PRODUCT:

    business/   a MARKET.        What can I buy, from whom, near me.
    supplier/   a DEMAND SIGNAL. Who is buying, who has gone quiet,
                                 what is stopping me selling.

V2_04 3.1 names mirroring one onto the other as the mistake that
started V2: "a supplier does not shop. Handing them a For You rail of
other suppliers is symmetry mistaken for design."

WHY THIS NEEDS A TEST AND NOT A CONVENTION. The risk was never that
somebody disagrees with that sentence -- it is FILENAMES. Both feeds
lived side by side in services/ as business_sections.py and
supplier_sections.py. Add a pipeline, sources, scoring and a demand
engine to one flat folder and eventually somebody writes

    from ..business.sections import collect_near_you

inside a supplier source, because the import looked plausible and the
file was right there. It would work, it would pass review on a busy
day, and the mirrored feed would be back.

THE RULES:

    core/       may import NEITHER role   (arranging knows nothing
                                          about who is reading)
    business/   may import core/, never supplier/
    supplier/   may import core/, never business/

core/ does not exist yet -- it arrives with the pipeline. Its rule is
written now because a test that appears at the same time as the code it
guards is an argument with code that already exists.

Parsed with AST rather than grepped, same discipline as the composer
and curtain tests: this codebase's comments discuss "business" and
"supplier" in prose constantly, so a text search would be noise.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator, List

BACKEND_ROOT = Path(__file__).resolve().parents[2]
COMMUNITY = BACKEND_ROOT / "src" / "domains" / "network" / "community"

BUSINESS_PKG = "src.domains.network.community.business"
SUPPLIER_PKG = "src.domains.network.community.supplier"
CORE_PKG = "src.domains.network.community.core"


def _python_files(root: Path) -> Iterator[Path]:
    if not root.exists():
        return
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        yield path


def _imported_modules(tree: ast.AST) -> Iterator[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def _offenders(root: Path, forbidden: str) -> List[str]:
    found: List[str] = []
    for path in _python_files(root):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for module in _imported_modules(tree):
            if module.startswith(forbidden):
                found.append(f"{path.relative_to(BACKEND_ROOT).as_posix()} -> {module}")
    return sorted(set(found))


def test_the_business_feed_does_not_import_the_supplier_feed() -> None:
    offenders = _offenders(COMMUNITY / "business", SUPPLIER_PKG)

    assert not offenders, (
        "The BUSINESS feed imported the SUPPLIER feed:\n  "
        + "\n  ".join(offenders)
        + "\n\nThese are two different products sharing a tab name. If both "
        "genuinely need the same computation, move THAT function into "
        "community/core/ or src/shared/algorithms/ -- do not reach across."
    )


def test_the_supplier_feed_does_not_import_the_business_feed() -> None:
    offenders = _offenders(COMMUNITY / "supplier", BUSINESS_PKG)

    assert not offenders, (
        "The SUPPLIER feed imported the BUSINESS feed:\n  "
        + "\n  ".join(offenders)
        + "\n\nThis is the direction that produces the mirrored feed V2_04 3.1 "
        "rejected: a supplier does not shop."
    )


def test_core_knows_about_neither_role() -> None:
    """core/ arranges Candidates into sections. The moment it can tell
    whose feed it is building, every future rule has somewhere
    role-specific to hide, and the shared engine stops being shared."""
    core = COMMUNITY / "core"
    offenders = _offenders(core, BUSINESS_PKG) + _offenders(core, SUPPLIER_PKG)

    assert not offenders, (
        "community/core/ reached into a role package:\n  "
        + "\n  ".join(offenders)
        + "\n\ncore/ is role-agnostic machinery. If it needs to know what it "
        "is arranging, the Candidate type should carry that, not an import."
    )


def test_the_role_packages_actually_exist() -> None:
    """Guards against the rules above passing vacuously -- three tests
    that assert nothing about empty directories would be worse than no
    tests, because they would look like coverage."""
    assert (COMMUNITY / "business" / "sections.py").exists()
    assert (COMMUNITY / "supplier" / "sections.py").exists()
