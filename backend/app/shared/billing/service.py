"""Billing and subscription business logic."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.shared.billing.schemas import (
    PlanTier,
    SubscriptionSchema,
    SubscriptionStatus,
    UsageSummary,
)

log = structlog.get_logger()

# Usage limits per plan tier
_LIMITS: dict[str, dict[str, float]] = {
    PlanTier.FREE: {
        "llm_tokens": 100_000,
        "video_minutes": 5.0,
        "storage_mb": 500.0,
    },
    PlanTier.PRO: {
        "llm_tokens": 5_000_000,
        "video_minutes": 60.0,
        "storage_mb": 10_000.0,
    },
    PlanTier.ENTERPRISE: {
        "llm_tokens": 100_000_000,
        "video_minutes": 1000.0,
        "storage_mb": 100_000.0,
    },
}


async def get_subscription(
    session: AsyncSession,
    user_id: str,
) -> SubscriptionSchema | None:
    result = await session.execute(
        text("""
            SELECT id, user_id, plan, status, current_period_start,
                   current_period_end, cancel_at_period_end, created_at
            FROM subscriptions
            WHERE user_id = :uid AND status IN ('active', 'trialing')
            ORDER BY created_at DESC LIMIT 1
        """),
        {"uid": user_id},
    )
    row = result.mappings().first()
    return SubscriptionSchema.model_validate(dict(row)) if row else None


async def ensure_free_subscription(
    session: AsyncSession,
    user_id: str,
) -> SubscriptionSchema:
    """Create a free-tier subscription if none exists."""
    existing = await get_subscription(session, user_id)
    if existing:
        return existing

    now = datetime.now(timezone.utc)
    sub_id = uuid4()
    result = await session.execute(
        text("""
            INSERT INTO subscriptions
                (id, user_id, plan, status, current_period_start, current_period_end, cancel_at_period_end)
            VALUES
                (:id, :uid, 'free', 'active', :start, :end, false)
            ON CONFLICT (user_id) DO NOTHING
            RETURNING id, user_id, plan, status, current_period_start,
                      current_period_end, cancel_at_period_end, created_at
        """),
        {
            "id": sub_id, "uid": user_id,
            "start": now,
            "end": now + timedelta(days=36500),  # free plan "never expires"
        },
    )
    await session.commit()
    row = result.mappings().first()
    if row:
        return SubscriptionSchema.model_validate(dict(row))
    return (await get_subscription(session, user_id))  # type: ignore[return-value]


async def log_usage(
    session: AsyncSession,
    user_id: str,
    resource_type: str,
    quantity: float,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record a usage event to usage_logs."""
    await session.execute(
        text("""
            INSERT INTO usage_logs (id, user_id, resource_type, quantity, metadata)
            VALUES (:id, :uid, :rtype, :qty, :meta::jsonb)
        """),
        {
            "id": uuid4(), "uid": user_id,
            "rtype": resource_type, "qty": quantity,
            "meta": _json_safe(metadata or {}),
        },
    )
    await session.commit()


async def get_usage_summary(
    session: AsyncSession,
    user_id: str,
) -> UsageSummary:
    """Aggregate current-period usage for the user."""
    sub = await get_subscription(session, user_id)
    plan = sub.plan if sub else PlanTier.FREE
    period_start = sub.current_period_start if sub else datetime.now(timezone.utc).replace(day=1)
    period_end = sub.current_period_end if sub else datetime.now(timezone.utc) + timedelta(days=30)

    result = await session.execute(
        text("""
            SELECT resource_type, COALESCE(SUM(quantity), 0) AS total
            FROM usage_logs
            WHERE user_id = :uid AND created_at >= :start AND created_at <= :end
            GROUP BY resource_type
        """),
        {"uid": user_id, "start": period_start, "end": period_end},
    )
    usage: dict[str, float] = {r["resource_type"]: r["total"] for r in result.mappings().all()}
    limits = _LIMITS.get(plan, _LIMITS[PlanTier.FREE])

    return UsageSummary(
        plan=plan,
        period_start=period_start,
        period_end=period_end,
        llm_tokens_used=int(usage.get("llm_tokens", 0)),
        llm_tokens_limit=int(limits["llm_tokens"]),
        video_minutes_used=usage.get("video_minutes", 0.0),
        video_minutes_limit=limits["video_minutes"],
        storage_mb_used=usage.get("storage_mb", 0.0),
        storage_mb_limit=limits["storage_mb"],
    )


async def check_quota(
    session: AsyncSession,
    user_id: str,
    resource_type: str,
    requested: float,
) -> bool:
    """Return True if the user has sufficient quota remaining."""
    summary = await get_usage_summary(session, user_id)
    if resource_type == "llm_tokens":
        return summary.llm_tokens_used + requested <= summary.llm_tokens_limit
    if resource_type == "video_minutes":
        return summary.video_minutes_used + requested <= summary.video_minutes_limit
    if resource_type == "storage_mb":
        return summary.storage_mb_used + requested <= summary.storage_mb_limit
    return True


def _json_safe(obj: Any) -> str:
    import json
    return json.dumps(obj, default=str)
