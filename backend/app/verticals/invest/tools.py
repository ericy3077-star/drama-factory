"""Investment-specific utility functions not tied to AgentOS tools."""
from __future__ import annotations

import re


def normalise_ticker(symbol: str) -> str:
    """
    Normalise a ticker symbol to uppercase ASCII, stripping whitespace.
    Raises ValueError if the result is not 1-10 characters.
    """
    cleaned = re.sub(r"[^A-Za-z0-9\.\-]", "", symbol.strip()).upper()
    if not 1 <= len(cleaned) <= 10:
        raise ValueError(f"Invalid ticker symbol: {symbol!r}")
    return cleaned


def format_market_cap(value: float | None) -> str:
    """Format a raw market cap number as a human-readable string."""
    if value is None:
        return "N/A"
    if value >= 1e12:
        return f"${value/1e12:.2f}T"
    if value >= 1e9:
        return f"${value/1e9:.2f}B"
    if value >= 1e6:
        return f"${value/1e6:.2f}M"
    return f"${value:,.0f}"


def sentiment_from_score(score: float) -> str:
    """Map a numeric sentiment score (-1 to 1) to a label."""
    if score >= 0.3:
        return "positive"
    if score <= -0.3:
        return "negative"
    return "neutral"


def parse_percentage(value: float | None, decimals: int = 2) -> str:
    """Format a ratio/decimal as a percentage string."""
    if value is None:
        return "N/A"
    return f"{value * 100:.{decimals}f}%"
