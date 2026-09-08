"""
ClaudeAIProvider -- THE ONLY FILE IN THIS CODEBASE THAT IMPORTS
`anthropic`.

That is the whole point of the provider abstraction, and it is checked
by an architecture test rather than left as a convention. Everything
else depends on AIProvider, so switching vendors, dropping to the fake,
or removing the dependency entirely is one function body in
composition.py.

NOTHING REACHES THIS FILE UNLESS AI_PROVIDER=claude. composition.py
imports it inside that branch, so a backend on the fake never loads the
SDK, never reads a key, and cannot be broken by a malformed one.

TWO MODELS, TWO SHAPES, AND THEY ARE NOT INTERCHANGEABLE:

  EXTRACTION runs on a small model (Haiku by default). Reading a line
  and filling in fields is not judgement. It uses a STRICT tool schema
  rather than asking for JSON and hoping -- a malformed response here
  becomes silent catalogue corruption, which is the failure the whole
  matching design is arranged to prevent.

  ADJUDICATION runs on a larger model with adaptive thinking and a
  configurable effort level, because "are these the same product?" is
  the decision that can make a price comparison a lie.

  Haiku does NOT accept adaptive thinking or an effort level -- passing
  either is an API error, not a no-op -- so those parameters are only
  sent to models that support them. See _supports_thinking.

THE PROVIDER NEVER DECIDES. adjudicate returns a confidence; the calling
domain's own gate decides what may be done with it. Keeping those
separate is what makes swapping in a cheaper model safe: it yields more
uncertainty, not more wrong answers.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import anthropic

from src.shared.ai.config import ai_config
from src.shared.ai.errors import AICallFailedError, AIProviderNotConfiguredError
from src.shared.ai.providers.provider import (
    AdjudicationResult,
    AIProvider,
    AIUsage,
    ExtractionResult,
)

logger = logging.getLogger(__name__)

#: Models that take adaptive thinking and an effort level. Haiku and
#: older models reject both outright, so this is a correctness check
#: rather than an optimisation.
_THINKING_MODELS = ("claude-opus-5", "claude-sonnet-5", "claude-opus-4-8", "claude-fable-5-1")

#: Generous but bounded. These are single structured calls, not agent
#: loops -- an extraction that wants more than this has gone wrong.
_MAX_TOKENS = 2048

_ADJUDICATION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "same": {
            "type": "boolean",
            "description": "True only if these are the same product in the same consumer size.",
        },
        "confidence": {
            "type": "number",
            "description": "0.0 to 1.0. Be honest about uncertainty; a low score is not a failure.",
        },
        "reason": {
            "type": "string",
            "description": "One sentence a shop owner would understand. No jargon, no scores.",
        },
    },
    "required": ["same", "confidence", "reason"],
    "additionalProperties": False,
}


def _supports_thinking(model: str) -> bool:
    return any(model.startswith(prefix) for prefix in _THINKING_MODELS)


class ClaudeAIProvider(AIProvider):
    def __init__(self) -> None:
        try:
            # Reads ANTHROPIC_API_KEY from the environment. Constructed
            # here rather than per call so the connection pool is reused
            # across a whole import.
            self._client = anthropic.Anthropic()
        except Exception as exc:  # pragma: no cover -- needs a broken env
            raise AIProviderNotConfiguredError(f"Could not construct the Anthropic client: {exc}") from exc

    @property
    def name(self) -> str:
        return "claude"

    # --- helpers -----------------------------------------------------------

    @staticmethod
    def _usage(response, model: str) -> AIUsage:
        """Real numbers off the response, never an estimate -- the budget
        ceiling is only as good as what feeds it."""
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) or 0
        output_tokens = getattr(usage, "output_tokens", 0) or 0
        cached = getattr(usage, "cache_read_input_tokens", 0) or 0
        return AIUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_input_tokens=cached,
            cost_cents=ai_config.cost_cents(
                model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_input_tokens=cached,
            ),
            model=model,
        )

    @staticmethod
    def _tool_input(response, tool_name: str) -> Dict[str, Any]:
        """The arguments of the tool call, parsed.

        PARSED WITH json, NEVER STRING-MATCHED. Tool input arrives as
        structured data but escaping varies between models, so anything
        that inspected the serialised form would be reading a moving
        target.
        """
        for block in getattr(response, "content", []) or []:
            if getattr(block, "type", None) == "tool_use" and getattr(block, "name", "") == tool_name:
                raw = getattr(block, "input", {})
                if isinstance(raw, str):
                    return json.loads(raw)
                return dict(raw or {})
        raise AICallFailedError(f"The model returned no {tool_name} call.")

    @staticmethod
    def _image_blocks(images: Optional[List[bytes]]) -> List[Dict[str, Any]]:
        import base64

        if not images:
            return []
        return [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(image).decode("ascii"),
                },
            }
            for image in images
        ]

    # --- the contract ------------------------------------------------------

    def extract(
        self,
        *,
        instruction: str,
        text: str,
        schema: Dict[str, Any],
        images: Optional[List[bytes]] = None,
    ) -> ExtractionResult:
        model = ai_config.extraction_model()
        tool = {
            "name": "record_fields",
            "description": "Record the fields read from the supplier's row.",
            "input_schema": schema,
            # THE GUARANTEE THAT THE SHAPE IS RIGHT. Without it the model
            # may return something schema-shaped but not schema-valid,
            # and a wrong field here is silent catalogue corruption.
            "strict": True,
        }

        content: List[Dict[str, Any]] = [*self._image_blocks(images), {"type": "text", "text": text}]

        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=_MAX_TOKENS,
                system=instruction,
                tools=[tool],
                messages=[{"role": "user", "content": content}],
            )
        except Exception as exc:
            raise AICallFailedError(f"Extraction failed: {exc}") from exc

        return ExtractionResult(
            data=self._tool_input(response, "record_fields"),
            usage=self._usage(response, model),
        )

    def adjudicate(
        self,
        *,
        instruction: str,
        left: str,
        right: str,
        images: Optional[List[bytes]] = None,
    ) -> AdjudicationResult:
        model = ai_config.adjudication_model()
        tool = {
            "name": "record_judgement",
            "description": "Record whether these are the same product, and how sure.",
            "input_schema": _ADJUDICATION_SCHEMA,
            "strict": True,
        }

        content: List[Dict[str, Any]] = [
            *self._image_blocks(images),
            {"type": "text", "text": f"A:\n{left}\n\nB:\n{right}"},
        ]

        request: Dict[str, Any] = {
            "model": model,
            "max_tokens": _MAX_TOKENS,
            "system": instruction,
            "tools": [tool],
            "messages": [{"role": "user", "content": content}],
        }
        if _supports_thinking(model):
            # Only for models that accept them -- Haiku rejects both.
            request["thinking"] = {"type": "adaptive"}
            request["output_config"] = {"effort": ai_config.adjudication_effort()}

        try:
            response = self._client.messages.create(**request)
        except Exception as exc:
            raise AICallFailedError(f"Adjudication failed: {exc}") from exc

        data = self._tool_input(response, "record_judgement")
        confidence = float(data.get("confidence", 0.0) or 0.0)
        return AdjudicationResult(
            same=bool(data.get("same", False)),
            # Clamped rather than trusted. A model returning 1.4 would
            # otherwise sail past an auto-link threshold it never
            # actually met.
            confidence=max(0.0, min(1.0, confidence)),
            reason=str(data.get("reason", ""))[:300],
            usage=self._usage(response, model),
        )
