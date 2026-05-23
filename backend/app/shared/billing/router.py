"""Billing API routes — Stripe Checkout + Webhook handling."""
from __future__ import annotations

import json
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.config import settings
from app.dependencies import CurrentUserId, DBSession
from app.shared.billing import service
from app.shared.billing.schemas import SubscriptionSchema, UsageSummary

log = structlog.get_logger()
router = APIRouter()


class CheckoutRequest(BaseModel):
    plan: str = "pro"  # "pro" | "enterprise"
    success_url: str = "http://localhost:3000/billing/success"
    cancel_url: str = "http://localhost:3000/billing/cancelled"


@router.get("/subscription", response_model=SubscriptionSchema | None)
async def get_subscription(user_id: CurrentUserId, session: DBSession) -> SubscriptionSchema | None:
    return await service.get_subscription(session, user_id)


@router.get("/usage", response_model=UsageSummary)
async def get_usage(user_id: CurrentUserId, session: DBSession) -> UsageSummary:
    return await service.get_usage_summary(session, user_id)


@router.post("/checkout")
async def create_checkout(
    body: CheckoutRequest,
    user_id: CurrentUserId,
    session: DBSession,
) -> dict[str, str]:
    """Create a Stripe Checkout Session and return the redirect URL."""
    if not settings.stripe_secret_key:
        # Dev mode: return placeholder
        return {
            "checkout_url": f"http://localhost:3000/billing/dev-success?plan={body.plan}",
            "session_id": "cs_dev_placeholder",
        }

    try:
        import stripe
        stripe.api_key = settings.stripe_secret_key

        price_id = (
            settings.stripe_price_id_enterprise
            if body.plan == "enterprise"
            else settings.stripe_price_id_pro
        )
        if not price_id:
            raise HTTPException(status_code=400, detail=f"No price configured for plan: {body.plan}")

        # Get or create Stripe customer
        sub = await service.get_subscription(session, user_id)
        customer_id = sub.stripe_customer_id if sub else None

        checkout_params: dict[str, Any] = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": body.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": body.cancel_url,
            "metadata": {"user_id": user_id, "plan": body.plan},
            "allow_promotion_codes": True,
        }
        if customer_id:
            checkout_params["customer"] = customer_id

        checkout_session = stripe.checkout.Session.create(**checkout_params)
        return {"checkout_url": checkout_session.url, "session_id": checkout_session.id}

    except ImportError:
        log.warning("billing.stripe_not_installed")
        return {
            "checkout_url": f"http://localhost:3000/billing/dev-success?plan={body.plan}",
            "session_id": "cs_dev_placeholder",
        }
    except stripe.StripeError as exc:  # type: ignore[attr-defined]
        log.error("billing.stripe_error", error=str(exc))
        raise HTTPException(status_code=502, detail=f"Stripe error: {exc.user_message}")


@router.post("/webhook")
async def stripe_webhook(request: Request, session: DBSession) -> dict[str, str]:
    """Receive Stripe webhook events and update subscription status."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not settings.stripe_secret_key:
        return {"received": "ok (dev mode)"}

    try:
        import stripe
        stripe.api_key = settings.stripe_secret_key

        if settings.stripe_webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        else:
            event = json.loads(payload)

        event_type = event["type"]
        log.info("billing.webhook_received", event_type=event_type)

        if event_type == "checkout.session.completed":
            evt_data = event["data"]["object"]
            uid = evt_data.get("metadata", {}).get("user_id")
            plan = evt_data.get("metadata", {}).get("plan", "pro")
            stripe_sub_id = evt_data.get("subscription")
            stripe_cust_id = evt_data.get("customer")
            if uid:
                await service.activate_subscription(
                    session, uid, plan, stripe_sub_id, stripe_cust_id
                )

        elif event_type == "customer.subscription.deleted":
            stripe_sub_id = event["data"]["object"]["id"]
            await service.cancel_subscription_by_stripe_id(session, stripe_sub_id)

        elif event_type == "invoice.payment_failed":
            stripe_sub_id = event["data"]["object"].get("subscription")
            if stripe_sub_id:
                await service.mark_subscription_past_due(session, stripe_sub_id)

    except ImportError:
        pass
    except Exception as exc:
        log.error("billing.webhook_error", error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))

    return {"received": "ok"}


@router.post("/portal")
async def customer_portal(
    user_id: CurrentUserId,
    session: DBSession,
) -> dict[str, str]:
    """Create a Stripe Customer Portal session for plan management."""
    if not settings.stripe_secret_key:
        return {"url": "http://localhost:3000/billing"}

    try:
        import stripe
        stripe.api_key = settings.stripe_secret_key

        sub = await service.get_subscription(session, user_id)
        if not sub or not sub.stripe_customer_id:
            raise HTTPException(status_code=404, detail="No active Stripe subscription found")

        portal = stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url="http://localhost:3000/billing",
        )
        return {"url": portal.url}
    except ImportError:
        return {"url": "http://localhost:3000/billing"}
