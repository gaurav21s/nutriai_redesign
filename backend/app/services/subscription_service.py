"""Service layer for subscription and billing."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from app.core.subscription import (
    PERMISSION_KEYS,
    get_default_subscription_payload,
    get_demo_subscription_payload,
    get_tier_permissions,
    is_local_demo_user,
)
from app.core.exceptions import AuthorizationException, ConfigurationException, ExternalServiceException
from app.repositories.base import CompositeRepository
from app.schemas.subscriptions import (
    ConfirmCheckoutRequest,
    CreateCheckoutSessionRequest,
    CreateCheckoutSessionResponse,
    DemoUserRecord,
    PlanSummary,
    PricingCatalogResponse,
    SelectPlanRequest,
    SeedDemoUsersResponse,
    SubscriptionEvent,
    SubscriptionHistoryResponse,
    SubscriptionRecord,
    SubscriptionResponse,
)


@lru_cache(maxsize=1)
def get_plan_catalog() -> tuple[PlanSummary, ...]:
    return (
        PlanSummary(
            tier="free",
            label="Free",
            description="Core nutrition tools for everyday guidance.",
            features=[
                "Food insight and ingredient checker",
                "Basic meal and recipe generation",
                "Quiz and calculator history",
            ],
            price_usd={"currency": "USD", "amount": 0, "interval": "month"},
            price_inr={"currency": "INR", "amount": 0, "interval": "month"},
        ),
        PlanSummary(
            tier="plus",
            label="Plus",
            description="For users who want deeper planning and faster outputs.",
            recommended=True,
            features=[
                "Unlimited AI generations",
                "Priority processing lane",
                "Extended history and export support",
            ],
            price_usd={"currency": "USD", "amount": 12, "interval": "month"},
            price_inr={"currency": "INR", "amount": 799, "interval": "month"},
        ),
        PlanSummary(
            tier="pro",
            label="Pro",
            description="Advanced coaching and premium productivity controls.",
            features=[
                "Everything in Plus",
                "Advanced recommendation workflows",
                "Premium support and priority queue",
            ],
            price_usd={"currency": "USD", "amount": 29, "interval": "month"},
            price_inr={"currency": "INR", "amount": 1999, "interval": "month"},
        ),
    )

def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _normalize_subscription(record: dict) -> SubscriptionRecord:
    return SubscriptionRecord.model_validate(record)

@lru_cache(maxsize=1)
def _load_demo_users(path: str) -> tuple[dict, ...]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return ()
    rows: list[dict] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        if not row.get("clerk_user_id"):
            continue
        rows.append(row)
    return tuple(rows)


class SubscriptionService:
    def __init__(
        self,
        repository: CompositeRepository,
        stripe_secret_key: str = "",
        stripe_publishable_key: str = "",
        demo_users_file: Path | None = None,
        environment: str = "development",
        dev_user_id: str = "dev_user",
    ) -> None:
        self.repository = repository
        self.stripe_secret_key = stripe_secret_key
        self.stripe_publishable_key = stripe_publishable_key
        self.demo_users_file = demo_users_file or (Path(__file__).resolve().parents[1] / "data" / "demo_users.json")
        self.environment = environment
        self.dev_user_id = dev_user_id

    def is_local_demo_user(self, clerk_user_id: str) -> bool:
        return is_local_demo_user(self.environment, clerk_user_id, self.dev_user_id)

    async def list_plans(self) -> PricingCatalogResponse:
        return PricingCatalogResponse(
            plans=list(get_plan_catalog()),
            stripe_publishable_key=self.stripe_publishable_key or None,
        )

    async def get_current_subscription(self, clerk_user_id: str) -> SubscriptionResponse:
        row = await self.repository.get_subscription(clerk_user_id)
        if self.is_local_demo_user(clerk_user_id):
            expected_demo_payload = get_demo_subscription_payload()
            expected_permissions = expected_demo_payload["permissions"]
            if not row or not row.get("is_demo") or any(
                bool((row.get("permissions", {}) or {}).get(key)) != expected_permissions[key] for key in PERMISSION_KEYS
            ):
                row = await self.repository.upsert_subscription(
                    clerk_user_id,
                    expected_demo_payload,
                )
                await self.repository.add_subscription_event(
                    clerk_user_id,
                    "demo_subscription_initialized",
                    {"tier": expected_demo_payload["tier"]},
                )

        if row:
            tier = str(row.get("tier") or "free")
            expected_permissions = get_tier_permissions(tier)
            raw_permissions = row.get("permissions", {})
            permissions = raw_permissions if isinstance(raw_permissions, dict) else {}
            if any(bool(permissions.get(key)) != expected_permissions[key] for key in PERMISSION_KEYS):
                row = await self.repository.upsert_subscription(
                    clerk_user_id,
                    {
                        "tier": tier,
                        "status": str(row.get("status") or "active"),
                        "currency": str(row.get("currency") or "USD"),
                        "amount": float(row.get("amount") or 0),
                        "interval": str(row.get("interval") or "month"),
                        "permissions": expected_permissions,
                        "is_demo": bool(row.get("is_demo", False)),
                        "stripe_customer_id": row.get("stripe_customer_id"),
                        "stripe_subscription_id": row.get("stripe_subscription_id"),
                        "stripe_checkout_session_id": row.get("stripe_checkout_session_id"),
                    },
                )
            return SubscriptionResponse(subscription=_normalize_subscription(row))

        seed = await self.repository.upsert_subscription(
            clerk_user_id,
            get_default_subscription_payload(),
        )
        await self.repository.add_subscription_event(clerk_user_id, "subscription_initialized", {"tier": "free"})
        return SubscriptionResponse(subscription=_normalize_subscription(seed))

    async def list_history(self, clerk_user_id: str, limit: int = 50) -> SubscriptionHistoryResponse:
        rows = await self.repository.list_subscription_events(clerk_user_id, limit)
        return SubscriptionHistoryResponse(items=[SubscriptionEvent.model_validate(item) for item in rows])

    async def select_plan(self, clerk_user_id: str, payload: SelectPlanRequest) -> SubscriptionResponse:
        amount = 0.0
        for plan in get_plan_catalog():
            if plan.tier == payload.tier:
                amount = float(plan.price_usd.amount if payload.currency == "USD" else plan.price_inr.amount)
                break

        row = await self.repository.upsert_subscription(
            clerk_user_id,
            {
                "tier": payload.tier,
                "status": "active",
                "currency": payload.currency,
                "amount": amount,
                "interval": "month",
                "permissions": get_tier_permissions(payload.tier),
                "is_demo": False,
            },
        )

        await self.repository.add_subscription_event(
            clerk_user_id,
            "plan_selected",
            {"tier": payload.tier, "currency": payload.currency, "amount": amount},
        )

        return SubscriptionResponse(subscription=_normalize_subscription(row))

    async def create_checkout_session(
        self,
        clerk_user_id: str,
        payload: CreateCheckoutSessionRequest,
    ) -> CreateCheckoutSessionResponse:
        if not self.stripe_secret_key:
            raise ConfigurationException("STRIPE_SECRET_KEY is not configured")

        plan = None
        for item in get_plan_catalog():
            if item.tier == payload.tier:
                plan = item
                break

        if not plan:
            raise ValueError("Unknown plan tier")

        price = plan.price_usd if payload.currency == "USD" else plan.price_inr

        try:
            from stripe import StripeClient  # type: ignore
        except ModuleNotFoundError as exc:
            raise ConfigurationException("stripe package is required for checkout flows") from exc

        stripe_client = StripeClient(self.stripe_secret_key)

        metadata = {
            "clerk_user_id": clerk_user_id,
            "tier": payload.tier,
            "currency": payload.currency,
        }

        async def _create_session() -> object:
            return await asyncio.to_thread(
                stripe_client.checkout.sessions.create,
                {
                    "mode": "subscription",
                    "success_url": payload.success_url,
                    "cancel_url": payload.cancel_url,
                    "metadata": metadata,
                    "line_items": [
                        {
                            "quantity": 1,
                            "price_data": {
                                "currency": payload.currency.lower(),
                                "unit_amount": int(round(float(price.amount) * 100)),
                                "recurring": {"interval": "month"},
                                "product_data": {
                                    "name": f"NutriAI {plan.label}",
                                    "description": plan.description,
                                },
                            },
                        }
                    ],
                },
            )

        try:
            session = await _create_session()
        except Exception as exc:
            raise ExternalServiceException("Stripe checkout session creation failed", details={"reason": str(exc)}) from exc

        session_id = str(getattr(session, "id", ""))
        checkout_url = str(getattr(session, "url", ""))

        await self.repository.add_subscription_event(
            clerk_user_id,
            "checkout_started",
            {
                "session_id": session_id,
                "tier": payload.tier,
                "currency": payload.currency,
                "amount": float(price.amount),
            },
        )

        return CreateCheckoutSessionResponse(session_id=session_id, checkout_url=checkout_url)

    async def confirm_checkout(self, clerk_user_id: str, payload: ConfirmCheckoutRequest) -> SubscriptionResponse:
        if not self.stripe_secret_key:
            raise ConfigurationException("STRIPE_SECRET_KEY is not configured")

        try:
            from stripe import StripeClient  # type: ignore
        except ModuleNotFoundError as exc:
            raise ConfigurationException("stripe package is required for checkout flows") from exc

        stripe_client = StripeClient(self.stripe_secret_key)

        async def _retrieve_session() -> object:
            return await asyncio.to_thread(
                stripe_client.checkout.sessions.retrieve,
                payload.session_id,
                {"expand": ["customer", "subscription"]},
            )

        try:
            session = await _retrieve_session()
        except Exception as exc:
            raise ExternalServiceException("Stripe checkout session retrieval failed", details={"reason": str(exc)}) from exc

        metadata = dict(getattr(session, "metadata", {}) or {})
        session_clerk_user_id = str(metadata.get("clerk_user_id") or "")
        if session_clerk_user_id != clerk_user_id:
            raise AuthorizationException(
                "Checkout session does not belong to the authenticated user",
                details={"session_id": payload.session_id},
            )
        tier = str(metadata.get("tier", "plus"))
        currency = str(metadata.get("currency", "USD")).upper()

        selected_plan = next((plan for plan in get_plan_catalog() if plan.tier == tier), get_plan_catalog()[1])
        price = selected_plan.price_usd if currency == "USD" else selected_plan.price_inr

        status = "active" if str(getattr(session, "payment_status", "unpaid")) in {"paid", "no_payment_required"} else "incomplete"

        row = await self.repository.upsert_subscription(
            clerk_user_id,
            {
                "tier": tier,
                "status": status,
                "currency": currency,
                "amount": float(price.amount),
                "interval": "month",
                "permissions": get_tier_permissions(tier),
                "is_demo": False,
                "stripe_customer_id": str(getattr(session, "customer", "") or "") or None,
                "stripe_subscription_id": str(getattr(session, "subscription", "") or "") or None,
                "stripe_checkout_session_id": str(getattr(session, "id", "") or "") or None,
            },
        )

        await self.repository.add_subscription_event(
            clerk_user_id,
            "checkout_confirmed",
            {
                "session_id": payload.session_id,
                "tier": tier,
                "currency": currency,
                "status": status,
            },
        )

        return SubscriptionResponse(subscription=_normalize_subscription(row))

    async def seed_demo_users(self) -> SeedDemoUsersResponse:
        demo_permissions = {key: True for key in PERMISSION_KEYS}
        now_iso = _now_iso()

        demo_users = list(_load_demo_users(str(self.demo_users_file)))

        results: list[DemoUserRecord] = []
        for user in demo_users:
            user_tier = str(user.get("tier") or "pro")
            user_email = str(user.get("email") or "")
            user_name = str(user.get("name") or "Demo User")
            user_created_at = str(user.get("created_at") or now_iso)
            user_id = str(user.get("clerk_user_id") or "")

            saved_user = await self.repository.upsert_user(
                user_id,
                {
                    "email": user_email,
                    "name": user_name,
                    "permissions": demo_permissions,
                    "is_demo": True,
                    "tier": user_tier,
                    "created_at": user_created_at,
                },
            )

            await self.repository.upsert_subscription(
                user_id,
                {
                    "tier": user_tier,
                    "status": "active",
                    "currency": "USD",
                    "amount": 0,
                    "interval": "month",
                    "permissions": demo_permissions,
                    "is_demo": True,
                },
            )

            await self.repository.add_subscription_event(
                user_id,
                "demo_seeded",
                {"tier": user_tier, "source": "seed_demo_users"},
            )

            results.append(
                DemoUserRecord(
                    clerk_user_id=user_id,
                    email=str(saved_user.get("email") or user_email),
                    name=str(saved_user.get("name") or user_name),
                    permissions=demo_permissions,
                    tier=user_tier,  # type: ignore[arg-type]
                    created_at=saved_user.get("created_at") or user_created_at,
                )
            )

        return SeedDemoUsersResponse(users=results)
