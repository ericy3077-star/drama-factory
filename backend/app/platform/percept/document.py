"""Document parsing utilities for PerceptOS."""
from __future__ import annotations

import io
from typing import Any

import httpx
import structlog
from bs4 import BeautifulSoup

log = structlog.get_logger()


async def extract_text_from_url(url: str) -> tuple[str, dict[str, Any]]:
    """
    Fetch a URL and extract readable text content.
    Strips HTML tags, scripts, and style elements.
    Returns (text, metadata).
    """
    async with httpx.AsyncClient(
        timeout=20,
        follow_redirects=True,
        headers={"User-Agent": "drama-factory/0.1 (research bot)"},
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")

        if "application/pdf" in content_type:
            text, meta = await parse_document(resp.content, "pdf")
            return text, {**meta, "url": url}

        soup = BeautifulSoup(resp.text, "lxml")

        # Remove noise elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Try to find main article content
        main = (
            soup.find("article")
            or soup.find("main")
            or soup.find(id="content")
            or soup.find(class_="content")
            or soup.body
        )

        text = main.get_text(separator="\n", strip=True) if main else soup.get_text("\n", strip=True)

        # Collapse excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        meta: dict[str, Any] = {
            "url": url,
            "title": soup.title.string.strip() if soup.title else "",
            "char_count": len(clean_text),
        }
        return clean_text, meta


async def parse_document(
    source: bytes | str,
    doc_type: str,
) -> tuple[str, dict[str, Any]]:
    """
    Parse a document from bytes or a file path.
    Supports: pdf, txt.
    """
    if doc_type == "pdf":
        return await _parse_pdf(source)  # type: ignore[arg-type]
    if doc_type in ("txt", "text"):
        text = source.decode() if isinstance(source, bytes) else source
        return text, {"char_count": len(text)}
    raise ValueError(f"Unsupported document type: {doc_type}")


async def _parse_pdf(source: bytes | str) -> tuple[str, dict[str, Any]]:
    """
    Extract text from a PDF.
    Accepts raw bytes or a URL string.
    """
    try:
        import pypdf  # optional dependency
    except ImportError:
        log.warning("parse_pdf.missing_pypdf")
        return "[PDF parsing requires pypdf: pip install pypdf]", {}

    if isinstance(source, str):
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(source)
            resp.raise_for_status()
            pdf_bytes = resp.content
    else:
        pdf_bytes = source

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")

    full_text = "\n".join(pages_text)
    return full_text, {"page_count": len(reader.pages), "char_count": len(full_text)}
