"""
ARCHITECTURE BOUNDARY TEST -- the demand engine cannot see suppliers.

THE INVARIANT THAT MAKES IT AN ENGINE (docs/v2/V2_15, Book Three):

    THE ENGINE ASKS "WHAT DOES THIS SHOP NEED?" AND THE ANSWER NEVER
    CONTAINS A SUPPLIER.

Test it by deleting every supplier on the platform. The shop model is
unchanged -- this shop still sells bread, still restocks twice a week,
still spends R1,400 a week. Only the separate question "who can supply
that" goes empty.

WHY THIS IS ENFORCED RATHER THAN TRUSTED. The moment the engine can see
who a supplier is, every future feature has a cheap way to favour one:
a "trusted partner" boost, a "premium supplier" weight, a tie-break on
catalogue size. Each is individually defensible, each ships on a busy
week, and together they are a marketplace that quietly sells its own
results. Not being able to SEE the supplier is what makes that
impossible rather than merely discouraged.

IT ALSO PROTECTS THE ANTI-DOMINATION PROPERTY. A demand model built
from what a SHOP needs returns, say, eleven products -- and that number
comes from the shop. A wholesaler who uploads ten thousand rows can
satisfy more of those eleven; they cannot make the shop need a twelfth.
That only holds while supply cannot reach into the model.

Parsed with AST, same discipline as the composer, curtain and feed-role
tests: "supplier" appears in this codebase's prose constantly, so a
text search would be noise.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator, List

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEMAND_ROOT = BACKEND_ROOT / "src" / "domains" / "business" / "demand"

#: Anything that knows who a supplier is.
FORBIDDEN_PREFIXES = (
    "src.domains.supplier",
    "src.domains.network.connections",
    "src.domains.verification",
)

#: The catalogue is ALLOWED and the distinction is the whole design.
#: ProductCategory is a vocabulary for describing a NEED -- "this shop
#: buys bakery" -- and says nothing about who sells it. A catalogue
#: PRODUCT is likewise supplier-agnostic by construction: that is what
#: the matching ladder exists to produce.
ALLOWED_NOTE = "src.domains.catalogue"


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


def test_the_demand_engine_imports_no_supplier_anything() -> None:
    offenders: List[str] = []

    for path in _python_files(DEMAND_ROOT):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for module in _imported_modules(tree):
            if module.startswith(FORBIDDEN_PREFIXES):
                offenders.append(
                    f"{path.relative_to(BACKEND_ROOT).as_posix()} -> {module}"
                )

    assert not offenders, (
        "The demand engine reached for supply:\n  "
        + "\n  ".join(sorted(set(offenders)))
        + "\n\nThe model describes a SHOP and must be computable with zero "
        "suppliers on the platform. If you need to know what is available, "
        "that question belongs AFTER the engine, in supply resolution -- "
        f"the answer the engine returns names categories and {ALLOWED_NOTE} "
        "products, never a supplier."
    )


def test_the_demand_engine_actually_exists() -> None:
    """Guards against the rule above passing vacuously. A test that
    asserts nothing about an empty directory is worse than no test,
    because it reads as coverage."""
    assert DEMAND_ROOT.exists(), "src/domains/business/demand/ is missing"
    assert any(_python_files(DEMAND_ROOT)), "demand/ has no modules to check"
