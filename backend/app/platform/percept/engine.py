"""PerceptOS — multimodal perception engine."""
from __future__ import annotations

import base64
from typing import Any

import anthropic
import structlog

from app.config import settings
from app.platform.percept.document import extract_text_from_url, parse_document
from app.platform.percept.extractors import extract_entities
from app.platform.percept.router import route_model

log = structlog.get_logger()


class Entity:
    def __init__(self, name: str, entity_type: str, confidence: float = 1.0,
                 context: str = "") -> None:
        self.name = name
        self.entity_type = entity_type
        self.confidence = confidence
        self.context = context

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.entity_type,
            "confidence": self.confidence,
            "context": self.context,
        }


class ProcessedContent:
    def __init__(
        self,
        source: str,
        source_type: str,
        raw_text: str,
        summary: str,
        entities: list[Entity],
        model_used: str,
        metadata: dict[str, Any],
    ) -> None:
        self.source = source
        self.source_type = source_type
        self.raw_text = raw_text
        self.summary = summary
        self.entities = entities
        self.model_used = model_used
        self.metadata = metadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "source_type": self.source_type,
            "summary": self.summary,
            "entities": [e.to_dict() for e in self.entities],
            "model_used": self.model_used,
            "text_length": len(self.raw_text),
            "metadata": self.metadata,
        }


class PerceptEngine:
    """
    Multimodal content processor with intelligent model routing.

    Routing strategy:
    - claude-haiku-4-5   → short text, simple queries
    - claude-sonnet-4-5  → complex text, documents with images
    - gemini-1.5-pro     → long-form video transcripts, very long docs
    """

    async def process(
        self,
        user_id: str,
        source: str,
        source_type: str,
        extra_metadata: dict[str, Any] | None = None,
    ) -> ProcessedContent:
        """
        Ingest content from *source* (URL, raw text, or base64-encoded file).
        *source_type*: 'url' | 'text' | 'pdf' | 'image' | 'video_transcript'
        """
        log.info("percept.process", user_id=user_id, source_type=source_type)

        # Step 1: Extract raw text / bytes
        raw_text, has_image, file_metadata = await self._extract_raw(source, source_type)

        # Step 2: Route to optimal model
        model_id = await self.route_model(source_type, has_image, len(raw_text))
        log.info("percept.model_selected", model=model_id, length=len(raw_text))

        # Step 3: Summarise and extract entities in parallel
        summary, entities = await self._analyse(raw_text, source_type, model_id, has_image, source)

        metadata = {**(extra_metadata or {}), **file_metadata}
        return ProcessedContent(
            source=source[:500],
            source_type=source_type,
            raw_text=raw_text,
            summary=summary,
            entities=entities,
            model_used=model_id,
            metadata=metadata,
        )

    async def extract_entities(self, content: str) -> list[Entity]:
        """Extract named entities from *content* using Claude Haiku."""
        raw_entities = await extract_entities(content)
        return [
            Entity(
                name=e.get("name", ""),
                entity_type=e.get("type", "UNKNOWN"),
                confidence=e.get("confidence", 1.0),
                context=e.get("context", ""),
            )
            for e in raw_entities
        ]

    async def route_model(
        self,
        content_type: str,
        has_image: bool,
        length: int,
    ) -> str:
        """Determine the best Claude/Gemini model for given content characteristics."""
        return route_model(content_type, has_image, length)

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _extract_raw(
        self,
        source: str,
        source_type: str,
    ) -> tuple[str, bool, dict[str, Any]]:
        """Return (raw_text, has_image, metadata)."""
        if source_type == "url":
            text, meta = await extract_text_from_url(source)
            return text, False, meta

        if source_type == "text":
            return source, False, {"char_count": len(source)}

        if source_type == "pdf":
            text, meta = await parse_document(source, "pdf")
            return text, False, meta

        if source_type == "image":
            # source is a URL; we'll pass it directly to Claude vision
            return f"[image: {source}]", True, {"image_url": source}

        if source_type == "video_transcript":
            # source is raw transcript text
            return source, False, {"type": "transcript", "char_count": len(source)}

        return source, False, {}

    async def _analyse(
        self,
        raw_text: str,
        source_type: str,
        model_id: str,
        has_image: bool,
        image_url: str | None = None,
    ) -> tuple[str, list[Entity]]:
        """Call the appropriate model to summarise and extract entities."""
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        messages: list[dict[str, Any]] = []
        if has_image and image_url:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "url", "url": image_url}},
                    {"type": "text", "text": (
                        "Describe the key content of this image. "
                        "Then list all named entities (people, organisations, products, locations) "
                        "you can identify. Respond as JSON: {summary: str, entities: [{name, type, confidence}]}"
                    )},
                ],
            })
        else:
            truncated = raw_text[:15000]
            messages.append({
                "role": "user",
                "content": (
                    f"Summarise the following {source_type} content in 3-5 sentences, "
                    f"then list all named entities (person, org, product, location, concept). "
                    f"Respond as JSON: {{summary: str, entities: [{{name, type, confidence (0-1)}}]}}\n\n"
                    f"Content:\n{truncated}"
                ),
            })

        import json
        response = await client.messages.create(
            model=model_id,
            max_tokens=1500,
            messages=messages,
        )
        text = response.content[0].text  # type: ignore[union-attr]

        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            parsed = json.loads(text[start:end])
            summary = parsed.get("summary", "")
            raw_ents = parsed.get("entities", [])
            entities = [
                Entity(e.get("name", ""), e.get("type", "UNKNOWN"), e.get("confidence", 1.0))
                for e in raw_ents
            ]
            return summary, entities
        except Exception:
            return text[:500], []


# Module-level singleton
percept_engine = PerceptEngine()
