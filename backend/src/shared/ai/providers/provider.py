"""
AIProvider -- the contract every model vendor implements.

THIS IS WHAT KEEPS ANTHROPIC OUT OF THE DOMAIN. Exactly one file in this
codebase imports the `anthropic` package (claude_provider.py). Every
caller depends on this interface, so swapping vendors, switching to a
fake, or turning the whole thing off is one function body in
composition.py -- the same isolation shape as MediaProvider (Cloudinary),
PaymentProvider (PayFast) and GeocodingProvider (Mapbox), deliberately
mirrored rather than invented fresh.

IT KNOWS NOTHING ABOUT PRODUCTS. src/shared/ may not depend on domains,
and that constraint is doing real work here rather than being a rule for
its own sake: verification will need document extraction, bulk import
will need column mapping, and none of that should have to route around a
matching-shaped abstraction. The interface takes a schema and some text
and gives back structured data. What the fields MEAN is the caller's
business.

TWO CALL SHAPES, NOT ONE PER FEATURE.

  extract()    text (and optionally images) -> JSON matching a schema
  adjudicate() "are these the same thing?"  -> yes/no plus a confidence

Everything the platform needs from a model so far is one of those two.
Resisting a third until something genuinely does not fit is what stops
this becoming a per-feature wrapper collection.

WHY adjudicate() RETURNS A CONFIDENCE AND NOT A DECISION. The provider
never decides anything. It reports how sure it is; the domain's own gate
decides what may be done about that. Keeping those separate is what lets
a cheaper model be swapped in safely -- it produces more uncertainty, not
more wrong answers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AIUsage:
    """What a call consumed. Recorded on every result so spend is
    measured rather than estimated -- the budget ceiling is only as good
    as the numbers feeding it."""

    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    #: Real money, in cents, computed by the provider from its own
    #: pricing. Cents and integers, never floats -- the same money
    #: convention the rest of this codebase uses.
    cost_cents: int = 0
    model: str = ""


@dataclass(frozen=True)
class ExtractionResult:
    """Structured data pulled out of text.

    `data` is whatever the caller's schema asked for. This layer does not
    validate the MEANING of it -- that the pack size is plausible, that
    the brand exists -- because it has no way to know. It only guarantees
    the shape.
    """

    data: Dict[str, Any] = field(default_factory=dict)
    usage: AIUsage = field(default_factory=AIUsage)


@dataclass(frozen=True)
class AdjudicationResult:
    """A judgement plus how sure it is.

    `reason` must be readable by a person who is not an engineer -- it
    ends up in a review queue a human works through, and eventually in
    front of a supplier disputing a match. "0.87" is not a reason.
    """

    same: bool
    confidence: float
    reason: str = ""
    usage: AIUsage = field(default_factory=AIUsage)


class AIProvider(ABC):
    @abstractmethod
    def extract(
        self,
        *,
        instruction: str,
        text: str,
        schema: Dict[str, Any],
        images: Optional[List[bytes]] = None,
    ) -> ExtractionResult:
        """Pull structured fields out of text, shaped by `schema`.

        `schema` is JSON Schema. A provider is expected to CONSTRAIN the
        model to it rather than ask nicely and hope -- a malformed
        response here becomes silent catalogue corruption, which is the
        failure this whole design is arranged to prevent.
        """

    @abstractmethod
    def adjudicate(
        self,
        *,
        instruction: str,
        left: str,
        right: str,
        images: Optional[List[bytes]] = None,
    ) -> AdjudicationResult:
        """Are these two descriptions the same thing, and how sure?

        Images are CORROBORATION, never the deciding factor. Two pack
        sizes of the same drink look identical in a photograph, so a
        provider that weighted the picture over the text would confidently
        merge products that differ by a factor of four in price.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier recorded on every decision, so a bad run can
        be traced to the thing that made it."""
