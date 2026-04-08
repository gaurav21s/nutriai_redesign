"""Subscription and billing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthorizationException
from app.core.subscription import is_local_demo_user
from app.core.security import AuthContext, get_auth_context
from app.dependencies import default_rate_limit, get_subscription_service
from app.schemas.subscriptions import (
    ConfirmCheckoutRequest,
    CreateCheckoutSessionRequest,
    CreateCheckoutSessionResponse,
    PricingCatalogResponse,
    SeedDemoUsersResponse,
    SelectPlanRequest,
    SubscriptionHistoryResponse,
    SubscriptionResponse,
    SubscriptionUsageResponse,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get(
    "/plans",
    response_model=PricingCatalogResponse,
    summary="Get pricing plans",
    description="Returns Free, Plus, and Pro plans with monthly prices in INR and USD.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_plans(
    service: SubscriptionService = Depends(get_subscription_service),
) -> PricingCatalogResponse:
    return await service.list_plans()


@router.get(
    "/current",
    response_model=SubscriptionResponse,
    summary="Get current subscription",
    description="Returns current authenticated user's subscription state.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_current_subscription(
    auth: AuthContext = Depends(get_auth_context),
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    return await service.get_current_subscription(auth.clerk_user_id)


@router.get(
    "/usage",
    response_model=SubscriptionUsageResponse,
    summary="Get current subscription usage",
    description="Returns current billing-period usage against the authenticated user's plan limits.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_current_subscription_usage(
    auth: AuthContext = Depends(get_auth_context),
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionUsageResponse:
    return await service.get_current_usage(auth.clerk_user_id)


@router.get(
    "/history",
    response_model=SubscriptionHistoryResponse,
    summary="Get subscription history",
    description="Returns tracked subscription events for the authenticated user.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_subscription_history(
    limit: int = Query(default=50, ge=1, le=200),
    auth: AuthContext = Depends(get_auth_context),
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionHistoryResponse:
    return await service.list_history(auth.clerk_user_id, limit)


@router.post(
    "/select",
    response_model=SubscriptionResponse,
    summary="Select plan directly",
    description="Selects or switches the user's plan directly. Useful for free tier activation and testing.",
    dependencies=[Depends(default_rate_limit)],
)
async def select_plan(
    payload: SelectPlanRequest,
    auth: AuthContext = Depends(get_auth_context),
    settings: Settings = Depends(get_settings),
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    if payload.tier != "free" and not is_local_demo_user(
        settings.environment,
        auth.clerk_user_id,
        settings.dev_user_id,
    ):
        raise AuthorizationException(
            "Paid plans must be activated through checkout",
            details={"tier": payload.tier, "suggested_action": "Use Stripe checkout for paid plans"},
        )
    return await service.select_plan(auth.clerk_user_id, payload)


@router.post(
    "/checkout-session",
    response_model=CreateCheckoutSessionResponse,
    summary="Create Stripe checkout session",
    description="Creates a Stripe checkout session for Plus or Pro monthly plans.",
    dependencies=[Depends(default_rate_limit)],
)
async def create_checkout_session(
    payload: CreateCheckoutSessionRequest,
    auth: AuthContext = Depends(get_auth_context),
    service: SubscriptionService = Depends(get_subscription_service),
) -> CreateCheckoutSessionResponse:
    return await service.create_checkout_session(auth.clerk_user_id, payload)


@router.post(
    "/checkout/confirm",
    response_model=SubscriptionResponse,
    summary="Confirm checkout completion",
    description="Fetches Stripe checkout session status and persists subscription in Convex.",
    dependencies=[Depends(default_rate_limit)],
)
async def confirm_checkout(
    payload: ConfirmCheckoutRequest,
    auth: AuthContext = Depends(get_auth_context),
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    return await service.confirm_checkout(auth.clerk_user_id, payload)


@router.post(
    "/demo-users/seed",
    response_model=SeedDemoUsersResponse,
    summary="Seed demo users",
    description="Creates two demo users with all permissions enabled for testing in development/local environments.",
    dependencies=[Depends(default_rate_limit)],
)
async def seed_demo_users(
    auth: AuthContext = Depends(get_auth_context),
    settings: Settings = Depends(get_settings),
    service: SubscriptionService = Depends(get_subscription_service),
) -> SeedDemoUsersResponse:
    if settings.environment not in {"local", "development"}:
        raise AuthorizationException("Demo user seeding is only allowed in local/development")

    if not settings.auth_disabled and auth.clerk_user_id not in {"dev_user", "demo_user_1", "demo_user_2"}:
        raise AuthorizationException("Only allowed test users can seed demo accounts")

    return await service.seed_demo_users()
