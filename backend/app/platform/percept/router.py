"""Model routing logic for PerceptOS."""
from __future__ import annotations

# Token-length thresholds for routing decisions
_SHORT_THRESHOLD = 2000       # < 2k chars → Haiku
_LONG_THRESHOLD = 50_000      # > 50k chars → Gemini

# Model identifiers
HAIKU = "claude-haiku-4-5"
SONNET = "claude-sonnet-4-5"
GEMINI = "gemini-1.5-pro"


def route_model(
    content_type: str,
    has_image: bool,
    length: int,
) -> str:
    """
    Determine the most cost-effective model for the given content profile.

    Rules (in priority order):
    1. Video transcripts or very long docs (>50k chars) → Gemini (large context window)
    2. Content with images → Sonnet (vision capability)
    3. Complex document types (PDF, research) → Sonnet
    4. Short text → Haiku (fast & cheap)
    5. Default medium text → Sonnet
    """
    if content_type == "video_transcript" or length > _LONG_THRESHOLD:
        return GEMINI

    if has_image:
        return SONNET

    if content_type in ("pdf", "research", "report"):
        return SONNET

    if length < _SHORT_THRESHOLD:
        return HAIKU

    return SONNET
