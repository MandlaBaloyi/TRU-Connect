"""
ARCHITECTURE BOUNDARY TESTS -- the AI layer's isolation, enforced.

TWO RULES, BOTH OF WHICH DECAY WITHOUT A TEST:

  1. shared/ai MUST NOT KNOW ABOUT DOMAINS. The moment it imports a
     catalogue type, it stops being reusable by verification, by column
     mapping, or by anything else that needs a model later -- and the
     next feature either duplicates it or bends the abstraction into a
     product-matching shape.

  2. EXACTLY ONE FILE MAY IMPORT `anthropic`. That is the entire value
     of the provider abstraction: swapping vendors, dropping to the fake
     or removing the dependency is one function body. An `import
     anthropic` anywhere else silently converts a swappable choice into
     a permanent one, and nobody notices until the day it matters.

Parsed with Python's own AST rather than searched as text -- a regex
would miss aliased or multi-line imports and would false-positive on the
word appearing in a docstring, which in this codebase it does, often.

Same discipline as test_finance_boundaries.py, deliberately mirrored:
verify the STRUCTURE, not just the behaviour.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator, List, Tuple

BACKEND_ROOT = Path(__file__).resolve().parents[2]
AI_ROOT = BACKEND_ROOT / "src" / "shared" / "ai"

#: shared/ai may import ONLY these from inside the project. It is a
#: leaf: things depend on it, it depends on almost nothing.
#:
#: src.extensions IS ALLOWED, and it is the one concession. It is the
#: Flask/SQLAlchemy registry -- where `db` lives -- not a domain, and the
#: decision ledger is a real table so it genuinely needs it. This list
#: started as a copy of the finance one, which does not include it
#: because finance owns no tables; the first run of this test caught the
#: difference. Adding it here is the correct fix, and the rules that
#: matter are untouched: no domain, and no vendor SDK outside the one
#: provider file.
ALLOWED_INTERNAL_PREFIXES = (
    "src.shared.ai",
    "src.core",
    "src.extensions",
)

#: The one file allowed to know a vendor exists, relative to AI_ROOT.
VENDOR_FILE = Path("providers/claude_provider.py")

#: Vendor SDKs. Adding a second provider means adding its package here
#: and giving it its own file -- never importing it from a shared one.
VENDOR_PACKAGES = ("anthropic", "openai", "google.generativeai", "cohere", "mistralai")


def _python_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" not in path.parts:
            yield path


def _imported_modules(path: Path) -> Iterator[Tuple[str, int]]:
    """Every module name this file imports, with its line number."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno
        elif isinstance(node, ast.ImportFrom):
            # A relative import (level > 0) cannot reach outside the
            # package, so it cannot cross a boundary.
            if node.module and node.level == 0:
                yield node.module, node.lineno


def test_the_ai_layer_never_imports_a_domain():
    violations: List[str] = []

    for path in _python_files(AI_ROOT):
        for module, line in _imported_modules(path):
            if not module.startswith("src."):
                continue
            if module.startswith(ALLOWED_INTERNAL_PREFIXES):
                continue
            violations.append(f"{path.relative_to(BACKEND_ROOT)}:{line} imports {module}")

    assert not violations, (
        "shared/ai must not depend on any domain -- it is infrastructure, and the\n"
        "whole reason it is shared is that verification and bulk import will need it\n"
        "too. It may import only: " + ", ".join(ALLOWED_INTERNAL_PREFIXES) + ".\n\n"
        + "\n".join(violations)
    )


def test_only_one_file_imports_a_vendor_sdk():
    violations: List[str] = []

    for path in _python_files(AI_ROOT):
        if path.relative_to(AI_ROOT) == VENDOR_FILE:
            continue
        for module, line in _imported_modules(path):
            root_package = module.split(".")[0]
            if root_package in VENDOR_PACKAGES or module in VENDOR_PACKAGES:
                violations.append(f"{path.relative_to(BACKEND_ROOT)}:{line} imports {module}")

    assert not violations, (
        f"Only {VENDOR_FILE} may import a vendor SDK. Everything else depends on the\n"
        "AIProvider interface, which is what makes the vendor swappable at one\n"
        "composition point instead of everywhere.\n\n" + "\n".join(violations)
    )


def test_no_vendor_sdk_is_imported_anywhere_outside_the_ai_layer():
    """The rule is only worth having if it holds across the whole
    backend. A domain importing anthropic directly would bypass the
    budget ceiling, the dry-run switch and the decision ledger all at
    once."""
    violations: List[str] = []
    src_root = BACKEND_ROOT / "src"

    for path in _python_files(src_root):
        if AI_ROOT in path.parents or path.parent == AI_ROOT:
            continue
        for module, line in _imported_modules(path):
            root_package = module.split(".")[0]
            if root_package in VENDOR_PACKAGES:
                violations.append(f"{path.relative_to(BACKEND_ROOT)}:{line} imports {module}")

    assert not violations, (
        "A vendor SDK may only be reached through shared/ai. Importing one directly\n"
        "bypasses the budget ceiling, the dry-run switch and the decision ledger.\n\n"
        + "\n".join(violations)
    )
