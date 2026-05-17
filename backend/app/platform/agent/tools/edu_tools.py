"""Education-domain tools for AgentOS."""
from __future__ import annotations

import anthropic
import structlog

from app.config import settings

log = structlog.get_logger()

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def search_learning_resources(
    topic: str,
    level: str = "beginner",
    max_results: int = 5,
) -> list[dict[str, str]]:
    """
    Search for learning resources about *topic*.
    Uses Claude to generate structured resource recommendations.
    """
    client = _get_client()
    prompt = (
        f"List {max_results} high-quality, freely available learning resources about '{topic}' "
        f"for a {level} learner. For each resource provide: title, url (real or plausible), "
        f"type (video/article/course/book), and a one-sentence description. "
        f"Respond as a JSON array."
    )
    message = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    import json
    try:
        text = message.content[0].text  # type: ignore[union-attr]
        # Extract JSON array from the response
        start = text.find("[")
        end = text.rfind("]") + 1
        return json.loads(text[start:end]) if start != -1 else []
    except Exception as exc:
        log.warning("search_learning_resources.parse_error", error=str(exc))
        return []


async def generate_quiz(
    topic: str,
    num_questions: int = 5,
    difficulty: str = "medium",
) -> list[dict[str, object]]:
    """
    Generate a multiple-choice quiz on *topic* using Claude.
    Returns a list of question dicts with: question, options (A-D), answer, explanation.
    """
    client = _get_client()
    prompt = (
        f"Create a {difficulty}-difficulty quiz with {num_questions} multiple-choice questions "
        f"about '{topic}'. Each question must have 4 options (A, B, C, D), a correct answer, "
        f"and a brief explanation. Respond as a JSON array of objects with keys: "
        f"question, options (object with A/B/C/D keys), answer (letter), explanation."
    )
    message = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    import json
    try:
        text = message.content[0].text  # type: ignore[union-attr]
        start = text.find("[")
        end = text.rfind("]") + 1
        return json.loads(text[start:end]) if start != -1 else []
    except Exception as exc:
        log.warning("generate_quiz.parse_error", error=str(exc))
        return []


async def summarize_document(content: str, max_words: int = 200) -> dict[str, str]:
    """
    Summarize *content* into key points using Claude Haiku.
    Returns {summary, key_points, takeaway}.
    """
    client = _get_client()
    prompt = (
        f"Summarize the following document in no more than {max_words} words. "
        f"Also extract 3-5 bullet-point key points and one actionable takeaway.\n\n"
        f"Respond as JSON with keys: summary, key_points (array), takeaway.\n\n"
        f"Document:\n{content[:8000]}"
    )
    message = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    import json
    try:
        text = message.content[0].text  # type: ignore[union-attr]
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end]) if start != -1 else {"summary": text}
    except Exception as exc:
        log.warning("summarize_document.parse_error", error=str(exc))
        return {"summary": "", "error": str(exc)}


async def create_course_outline(
    topic: str,
    duration_weeks: int = 4,
    level: str = "beginner",
) -> dict[str, object]:
    """
    Generate a structured course outline for *topic* using Claude.
    Returns {title, description, modules: [{week, title, objectives, lessons}]}.
    """
    client = _get_client()
    prompt = (
        f"Design a {duration_weeks}-week online course outline about '{topic}' for {level} learners. "
        f"For each week provide: week number, module title, 2-3 learning objectives, "
        f"and 3-4 lesson titles. Respond as JSON with keys: "
        f"title, description, target_audience, modules (array)."
    )
    message = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    import json
    try:
        text = message.content[0].text  # type: ignore[union-attr]
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end]) if start != -1 else {}
    except Exception as exc:
        log.warning("create_course_outline.parse_error", error=str(exc))
        return {"error": str(exc)}
