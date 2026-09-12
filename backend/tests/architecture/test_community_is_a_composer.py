"""
ARCHITECTURE BOUNDARY TEST -- the Community feed is a COMPOSER.

THE RULE, stated in V2_04 Part 5 and required to ship in the same
commit as the domain rather than "later":

    the feed service may import from domain repositories, but NO
    DOMAIN MAY IMPORT THE FEED SERVICE. It is a composer, and the
    coordinator never gets imported by the thing it coordinates.

WHY IT NEEDS A TEST AND NOT A CODE REVIEW. The violation is always
convenient at the moment somebody writes it. The supplier profile
service will one day want "how many businesses are near me", the
orders domain will want "is this customer overdue" -- both already
computed here, both one import away. Each of those imports is three
seconds of work and turns a leaf into a cycle, and the failure is
invisible until the day a change to the feed breaks checkout for
reasons nobody can trace.

THE SECOND RULE, which is the same one from the other side: the feed
must not own tables. A composer that persists things has stopped
composing and started being a domain, and the moment it has its own
rows every other domain acquires a reason to read them. V2_04 allows
exactly one future exception -- impression logging -- and that is a
different concern from composition.

Parsed with Python's AST rather than grepped, same discipline as
test_ai_boundaries.py: this codebase's comments mention "community"
and "feed_service" in prose often enough that a text search would be
noise.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator, List

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DOMAINS_ROOT = BACKEND_ROOT / "src" / "domains"
SHARED_ROOT = BACKEND_ROOT / "src" / "shared"
COMMUNITY_ROOT = DOMAINS_ROOT / "network" / "community"

#: The import path nothing outside the feed may reach for.
COMMUNITY_MODULE = "src.domains.network.community"


def _python_files(root: Path) -> Iterator[Path]:
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


def test_no_domain_imports_the_feed() -> None:
    """RULE 1. The coordinator is not imported by what it coordinates."""
    offenders: List[str] = []

    for root in (DOMAINS_ROOT, SHARED_ROOT):
        for path in _python_files(root):
            if COMMUNITY_ROOT in path.parents or path.parent == COMMUNITY_ROOT:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for module in _imported_modules(tree):
                if module.startswith(COMMUNITY_MODULE):
                    offenders.append(f"{path.relative_to(BACKEND_ROOT).as_posix()} -> {module}")

    assert not offenders, (
        "Something imported the Community feed. It is a COMPOSER -- it reads "
        "from domains, and no domain may read from it:\n  "
        + "\n  ".join(sorted(set(offenders)))
        + "\n\nIf a domain needs a computation the feed does (reorder gap, "
        "distance), move THAT function somewhere both can import -- do not "
        "import the composer."
    )


def test_the_feed_owns_no_tables() -> None:
    """RULE 2. A composer that persists has stopped composing.

    V2_04 allows exactly one future exception, impression logging, and
    that is a different concern -- when it lands it gets its own
    reasoning, not this test quietly deleted.
    """
    offenders: List[str] = []

    for path in _python_files(COMMUNITY_ROOT):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for base in node.bases:
                name = base.attr if isinstance(base, ast.Attribute) else getattr(base, "id", "")
                if name in ("Model", "BaseModel"):
                    offenders.append(
                        f"{path.relative_to(BACKEND_ROOT).as_posix()}:{node.lineno} {node.name}"
                    )

    assert not offenders, (
        "The Community feed declared a model. It owns no tables:\n  "
        + "\n  ".join(offenders)
    )


def test_ordering_lives_in_one_file() -> None:
    """V2_04 Part 5: "The composition rules live in a single service so
    ordering is one file, not scattered."

    Checked structurally rather than by reading: only feed_service may
    assemble the section list. A section builder that started ordering
    its own output would make "why is this rail second?" a question you
    answer by reading four files and guessing.
    """
    feed_service = COMMUNITY_ROOT / "services" / "feed_service.py"
    assert feed_service.exists(), "the one ordering file is missing"

    source = feed_service.read_text(encoding="utf-8")
    assert "wants_to_connect" in source and "businesses_near_you" in source, (
        "feed_service no longer names the sections it orders -- if ordering "
        "moved, this test and V2_04 Part 5 both need updating"
    )
