"""Pydantic v2 schemas for billing and subscriptions."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class PlanTier(StrEnum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class SubscriptionSchema(BaseModel):
    id: UUID
    user_id: str
    plan: PlanTier
    status: SubscriptionStatus
    stripe_subscription_id: str | None = None
    stripe_customer_id: str | None = None
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageLogSchema(BaseModel):
    id: UUID
    user_id: str
    resource_type: str  # 'llm_tokens' | 'video_minutes' | 'storage_mb'
    quantity: float
    metadata: dict[str, object]
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageSummary(BaseModel):
    plan: str
    period_start: datetime
    period_end: datetime
    llm_tokens_used: int
    llm_tokens_limit: int
    video_minutes_used: float
    video_minutes_limit: float
    storage_mb_used: float
    storage_mb_limit: float


class CheckoutRequest(BaseModel):
    plan: PlanTier
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class WebhookEvent(BaseModel):
    event_type: str
    data: dict[str, object]
