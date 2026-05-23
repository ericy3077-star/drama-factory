"""Billing quota and usage tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.shared.billing.service import check_quota


@pytest.mark.asyncio
async def test_check_quota_within_limit(mock_session) -> None:
    """check_quota returns True when usage is below limit."""
    mock_summary = MagicMock()
    mock_summary.llm_tokens_used = 50_000
    mock_summary.llm_tokens_limit = 100_000

    with patch(
        "app.shared.billing.service.get_usage_summary",
        new_callable=AsyncMock,
        return_value=mock_summary,
    ):
        ok = await check_quota(mock_session, "user-1", "llm_tokens", 10_000)

    assert ok is True


@pytest.mark.asyncio
async def test_check_quota_exceeded(mock_session) -> None:
    """check_quota returns False when adding requested amount would exceed limit."""
    mock_summary = MagicMock()
    mock_summary.llm_tokens_used = 95_000
    mock_summary.llm_tokens_limit = 100_000

    with patch(
        "app.shared.billing.service.get_usage_summary",
        new_callable=AsyncMock,
        return_value=mock_summary,
    ):
        ok = await check_quota(mock_session, "user-1", "llm_tokens", 10_000)

    assert ok is False
