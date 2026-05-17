"""Billing API routes."""
from __future__ import annotations

from fastapi import APIRouter, status

from app.dependencies import CurrentUserId, DBSession
from app.shared.billing import service
from app.shared.billing.schemas import (
    SubscriptionSchema,
    UsageSummary,
)

router = APIRouter()


@router.get("/subscription", response_model=SubscriptionSchema | None)
async def get_subscription(
    user_id: CurrentUserId,
    session: DBSession,
) -> SubscriptionSchema | None:
    return await service.get_subscription(session, user_id)


@router.get("/usage", response_model=UsageSummary)
async def get_usage(
    user_id: CurrentUserId,
    session: DBSession,
) -> UsageSummary:
    return await service.get_usage_summary(session, user_id)


@router.post("/checkout", status_code=status.HTTP_200_OK)
async def create_checkout(
    user_id: CurrentUserId,
) -> dict[str, str]:
    """
    Stripe checkout session creation.
    Requires Stripe SDK integration — returns a placeholder in development.
    """
    return {
        "checkout_url": "https://checkout.stripe.com/pay/placeholder",
        "session_id": "cs_placeholder",
    }


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    session: DBSession,
) -> dict[str, str]:
    """
    Stripe webhook handler — update subscription status on payment events.
    In production, verify the Stripe-Signature header.
    """
    # Webhook processing logic would go here
    return {"received": "ok"}
