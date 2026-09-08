"""
FakeAIProvider -- what the entire test suite runs on, and the default
everywhere until someone deliberately configures otherwise.

THIS IS NOT A STUB, AND THE DISTINCTION MATTERS. A stub is a placeholder
for something unfinished. This is permanent infrastructure: if any test
in this codebase ever needs a real API key or a network connection to
pass, the design has gone wrong. Tests must be free, offline, fast and
deterministic, and this is what makes all four true at once.

Same role as MAIL_PROVIDER=fake and the media FakeMediaProvider that
test_media_api.py already uses -- and the same reasoning those record.

DETERMINISTIC, NOT RANDOM. Given the same input it returns the same
answer every time, so a test that passes today cannot fail on Tuesday.
The "judgement" below is a crude string comparison, which is exactly
right: the point is never that the fake is clever, it is that the code
AROUND the provider can be exercised without a model.

IT REPORTS ZERO COST, and every caller that adds usage up will therefore
see zero spend in tests. That is a feature -- a budget test that
accidentally billed real money would be worse than no budget test.

PROGRAMMABLE, so a test can pin an exact answer:

    provider = FakeAIProvider()
    provider.queue_adjudication(same=True, confidence=0.97)
"""
from __future__ import annotations

from collections import deque
from typing import Any, Deque, Dict, List, Optional

from src.shared.ai.providers.provider import (
    AdjudicationResult,
    AIProvider,
    AIUsage,
    ExtractionResult,
)


class FakeAIProvider(AIProvider):
    def __init__(self) -> None:
        self._extractions: Deque[Dict[str, Any]] = deque()
        self._adjudications: Deque[AdjudicationResult] = deque()
        #: Every call made, for tests that assert the model was NOT
        #: consulted -- which is most of them, since the free tiers are
        #: supposed to answer first.
        self.calls: List[Dict[str, Any]] = []

    @property
    def name(self) -> str:
        return "fake"

    # --- programming the fake ---------------------------------------------

    def queue_extraction(self, **data: Any) -> None:
        self._extractions.append(data)

    def queue_adjudication(self, *, same: bool, confidence: float, reason: str = "") -> None:
        self._adjudications.append(
            AdjudicationResult(same=same, confidence=confidence, reason=reason or "fake")
        )

    def clear(self) -> None:
        self._extractions.clear()
        self._adjudications.clear()
        self.calls.clear()

    # --- the contract ------------------------------------------------------

    def extract(
        self,
        *,
        instruction: str,
        text: str,
        schema: Dict[str, Any],
        images: Optional[List[bytes]] = None,
    ) -> ExtractionResult:
        self.calls.append({"kind": "extract", "text": text})
        if self._extractions:
            return ExtractionResult(data=self._extractions.popleft(), usage=AIUsage(model="fake"))

        # NOTHING QUEUED MEANS AN EMPTY RESULT, not an invented one. A
        # fake that guessed would let a test pass because the fake was
        # helpful rather than because the code was right.
        return ExtractionResult(data={}, usage=AIUsage(model="fake"))

    def adjudicate(
        self,
        *,
        instruction: str,
        left: str,
        right: str,
        images: Optional[List[bytes]] = None,
    ) -> AdjudicationResult:
        self.calls.append({"kind": "adjudicate", "left": left, "right": right})
        if self._adjudications:
            return self._adjudications.popleft()

        # A deliberately crude default so an un-programmed test still
        # gets a defensible answer: identical strings are the same
        # thing, anything else is uncertain rather than wrong. Uncertain
        # sends a row to the review queue, which is the safe direction.
        identical = left.strip().lower() == right.strip().lower()
        return AdjudicationResult(
            same=identical,
            confidence=1.0 if identical else 0.5,
            reason="Fake provider: exact string comparison only.",
            usage=AIUsage(model="fake"),
        )
