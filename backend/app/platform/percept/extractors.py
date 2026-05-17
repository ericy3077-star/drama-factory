"""Named entity extraction for PerceptOS."""
from __future__ import annotations

import json
from typing import Any

import anthropic
import structlog

from app.config import settings

log = structlog.get_logger()


async def extract_entities(
    content: str,
    entity_types: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Extract named entities from *content* using Claude Haiku.

    *entity_types*: list of types to focus on, e.g. ['PERSON', 'ORG', 'PRODUCT'].
    If None, all common types are extracted.

    Returns a list of dicts: [{name, type, confidence, context}].
    """
    types_hint = (
        ", ".join(entity_types)
        if entity_types
        else "PERSON, ORG, PRODUCT, LOCATION, EVENT, CONCEPT, TICKER, CURRENCY"
    )
    truncated = content[:8000]

    prompt = (
        f"Extract all named entities from the text below. "
        f"Focus on types: {types_hint}. "
        f"For each entity provide: name (exact text), type, confidence (0.0-1.0), "
        f"and a short context snippet (up to 50 chars surrounding the mention). "
        f"Return ONLY a JSON array. Example: "
        f'[{{"name":"Apple","type":"ORG","confidence":0.98,"context":"...Apple announced..."}}]\n\n'
        f"Text:\n{truncated}"
    )

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text  # type: ignore[union-attr]
    try:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1:
            return []
        entities: list[dict[str, Any]] = json.loads(text[start:end])
        # Normalise and deduplicate by (name.lower(), type)
        seen: set[tuple[str, str]] = set()
        result = []
        for e in entities:
            key = (e.get("name", "").lower(), e.get("type", ""))
            if key not in seen:
                seen.add(key)
                result.append({
                    "name": e.get("name", ""),
                    "type": e.get("type", "UNKNOWN"),
                    "confidence": min(1.0, max(0.0, float(e.get("confidence", 1.0)))),
                    "context": e.get("context", ""),
                })
        return result
    except Exception as exc:
        log.warning("extract_entities.parse_error", error=str(exc), raw=text[:200])
        return []


async def extract_financial_entities(content: str) -> list[dict[str, Any]]:
    """
    Specialised extractor for financial content.
    Focuses on: TICKER, COMPANY, SECTOR, METRIC, DATE, CURRENCY.
    """
    return await extract_entities(
        content,
        entity_types=["TICKER", "COMPANY", "SECTOR", "METRIC", "DATE", "CURRENCY"],
    )


async def extract_educational_entities(content: str) -> list[dict[str, Any]]:
    """
    Specialised extractor for educational content.
    Focuses on: CONCEPT, SKILL, PERSON, INSTITUTION, COURSE, TOOL.
    """
    return await extract_entities(
        content,
        entity_types=["CONCEPT", "SKILL", "PERSON", "INSTITUTION", "COURSE", "TOOL"],
    )
