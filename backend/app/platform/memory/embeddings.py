"""Vector embedding generation via Anthropic voyage or a local fallback."""
from __future__ import annotations

import hashlib
from typing import Any

import httpx

from app.config import settings

# Voyage-3 text embedding endpoint (Anthropic's embedding service)
VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
EMBED_MODEL = "voyage-3"
EMBED_DIMENSIONS = 1024  # voyage-3 native dimension; stored as vector(1024)


async def embed_text(text: str) -> list[float]:
    """Return a normalised embedding vector for *text*."""
    key = settings.voyage_api_key or settings.anthropic_api_key
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            VOYAGE_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={"input": [text], "model": EMBED_MODEL},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data["data"][0]["embedding"]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Return embeddings for a list of texts in a single API call."""
    if not texts:
        return []
    key = settings.voyage_api_key or settings.anthropic_api_key
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            VOYAGE_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={"input": texts, "model": EMBED_MODEL},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        # Sort by index to preserve order
        items = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in items]


def content_fingerprint(text: str) -> str:
    """SHA-256 fingerprint to detect duplicate content before embedding."""
    return hashlib.sha256(text.encode()).hexdigest()
