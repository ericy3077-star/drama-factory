"""HeyGen API wrapper — avatar creation and video generation."""
from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.config import settings

log = structlog.get_logger()

HEYGEN_BASE = "https://api.heygen.com"
_TIMEOUT = 30.0


def _headers() -> dict[str, str]:
    return {
        "X-Api-Key": settings.heygen_api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def create_avatar_from_photo(
    photo_url: str,
    name: str,
    gender: str = "neutral",
) -> dict[str, Any]:
    """
    Upload a talking-photo avatar to HeyGen.
    Returns HeyGen's avatar object including avatar_id.
    """
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{HEYGEN_BASE}/v2/photo_avatar",
            headers=_headers(),
            json={
                "image_url": photo_url,
                "name": name,
                "gender": gender,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def list_avatars() -> list[dict[str, Any]]:
    """Return all avatars belonging to the account."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(f"{HEYGEN_BASE}/v2/avatars", headers=_headers())
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("avatars", [])


async def generate_video(
    avatar_id: str,
    script: str,
    voice_id: str | None = None,
    language: str = "zh",
    resolution: str = "1080p",
) -> dict[str, Any]:
    """
    Submit a video generation request to HeyGen.
    Returns a task object with video_id and status.
    """
    voice_settings: dict[str, Any] = {"type": "text", "input_text": script}
    if voice_id:
        voice_settings["voice_id"] = voice_id

    payload: dict[str, Any] = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": voice_settings,
            }
        ],
        "dimension": {"width": 1920, "height": 1080} if resolution == "1080p" else {"width": 1280, "height": 720},
        "aspect_ratio": "16:9",
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{HEYGEN_BASE}/v2/video/generate",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def get_video_status(video_id: str) -> dict[str, Any]:
    """Poll the status of a video generation task."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(
            f"{HEYGEN_BASE}/v1/video_status.get",
            headers=_headers(),
            params={"video_id": video_id},
        )
        resp.raise_for_status()
        return resp.json()


async def delete_video(video_id: str) -> bool:
    """Delete a generated video from HeyGen storage."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.delete(
            f"{HEYGEN_BASE}/v1/video/{video_id}",
            headers=_headers(),
        )
        return resp.status_code == 200
