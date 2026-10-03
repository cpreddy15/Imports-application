"""Thin wrapper around the Anthropic SDK.

Every AI feature in TradeFlow has a deterministic fallback, so the platform
works end-to-end without an API key; setting ANTHROPIC_API_KEY upgrades the
results to Claude.
"""

import json
import logging
from typing import Any

import anthropic

from ..config import settings

log = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def enabled() -> bool:
    return bool(settings.anthropic_api_key)


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _request_kwargs(effort: str) -> dict[str, Any]:
    return {
        "model": settings.claude_model,
        "thinking": {"type": "adaptive"},
        # Re-run on a fallback model if the primary declines (policy refusal).
        "betas": ["server-side-fallback-2026-07-01"],
        "fallbacks": "default",
        "output_config": {"effort": effort},
    }


def _text(response: Any) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def structured(system: str, prompt: str, schema: dict, effort: str = "medium") -> dict | None:
    """Ask Claude for JSON matching `schema`. Returns None on any failure."""
    if not enabled():
        return None
    kwargs = _request_kwargs(effort)
    kwargs["output_config"]["format"] = {"type": "json_schema", "schema": schema}
    try:
        response = client().beta.messages.create(
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
    except anthropic.APIConnectionError as e:
        log.warning("Claude unreachable: %s", e)
        return None
    except anthropic.APIStatusError as e:
        log.warning("Claude API error %s: %s", e.status_code, e.message)
        return None
    if response.stop_reason in ("refusal", "max_tokens"):
        log.warning("Claude stopped with %s", response.stop_reason)
        return None
    try:
        return json.loads(_text(response))
    except json.JSONDecodeError:
        log.warning("Claude returned non-JSON output")
        return None


def chat(system: str, messages: list[dict], effort: str = "low") -> str | None:
    """Multi-turn chat completion. Returns None on any failure."""
    if not enabled():
        return None
    try:
        response = client().beta.messages.create(
            max_tokens=16000, system=system, messages=messages, **_request_kwargs(effort)
        )
    except anthropic.APIConnectionError as e:
        log.warning("Claude unreachable: %s", e)
        return None
    except anthropic.APIStatusError as e:
        log.warning("Claude API error %s: %s", e.status_code, e.message)
        return None
    if response.stop_reason == "refusal":
        return "I can't help with that request. Please rephrase or contact a licensed customs broker."
    return _text(response) or None
