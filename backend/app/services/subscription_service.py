"""Service layer for subscription, billing, and plan-based usage limits."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from app.core.subscription import (
    PERMISSION_KEYS,
    current_usage_period,
    get_default_subscription_payload,
    get_demo_subscription_payload,
    get_plan_amount,
    get_tier_limits,
    get_tier_permissions,
    is_local_demo_user,
    is_within_history_window,
)
from app.core.exceptions import AppException, AuthorizationException, ConfigurationException, ExternalServiceException
from app.repositories.base import CompositeRepository
from app.schemas.subscriptions import (
    ConfirmCheckoutRequest,
    CreateCheckoutSessionRequest,
    CreateCheckoutSessionResponse,
    DemoUserRecord,
    PlanLimits,
    PlanSummary,
    PricingCatalogResponse,
    SeedDemoUsersResponse,
    SelectPlanRequest,
    SubscriptionEvent,
    SubscriptionHistoryResponse,
    SubscriptionRecord,
    SubscriptionResponse,
    SubscriptionUsage,
    SubscriptionUsagePeriod,
    SubscriptionUsageResponse,
    UsageAllowance,
)


@lru_cache(maxsize=1)
def get_plan_catalog() -> tuple[PlanSummary, ...]:
    return (
        PlanSummary(
            tier="free",
            label="Free",
            description="Try NutriAI with light monthly usage across all major tools.",
            features=[
                "12 nutrition credits each month",
                "15 Nutri Chat messages each month",
                "30-day saved history",
            ],
            limits=PlanLimits.model_validate(get_tier_limits("free")),
            price_usd={"currency": "USD", "amount": 0, "interval": "month"},
            price_inr={"currency": "INR", "amount": 0, "interval": "month"},
        ),
        PlanSummary(
            tier="plus",
            label="Plus",
            description="Built for steady weekly planning without constant quota friction.",
            recommended=True,
            features=[
                "120 nutrition credits and 250 chat messages monthly",
                "Meal plan PDF export and 1-year history",
                "Priority processing for faster responses",
            ],
            limits=PlanLimits.model_validate(get_tier_limits("plus")),
            price_usd={"currency": "USD", "amount": 7.99, "interval": "month"},
            price_inr={"currency": "INR", "amount": 499, "interval": "month"},
        ),
        PlanSummary(
            tier="pro",
            label="Pro",
            description="For high-frequency users who want NutriAI in their daily workflow.",
            features=[
                "400 nutrition credits and 800 chat messages monthly",
                "Unlimited history with the largest chat context window",
                "50 PDF exports and priority support",
            ],
            limits=PlanLimits.model_validate(get_tier_limits("pro")),
            price_usd={"currency": "USD", "amount": 12.99, "interval": "month"},
            price_inr={"currency": "INR", "amount": 999, "interval": "month"},
        ),
    )


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _normalize_subscription(record: dict) -> SubscriptionRecord:
    if "limits" not in record:
        tier = record.get("tier", "free")
        record = {**record, "limits": get_tier_limits(tier)}
    if "permissions" not in record:
        tier = record.get("tier", "free")
        record = {**record, "permissions": get_tier_permissions(tier)}
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
            if self._subscription_needs_refresh(row, expected_demo_payload):
                row = await self.repository.upsert_subscription(clerk_user_id, expected_demo_payload)
                await self.repository.add_subscription_event(
                    clerk_user_id,
                    "demo_subscription_initialized",
                    {"tier": expected_demo_payload["tier"]},
                )

        if row:
            normalized = await self._refresh_subscription_row(clerk_user_id, row)
            return SubscriptionResponse(subscription=_normalize_subscription(normalized))

        seed = await self.repository.upsert_subscription(clerk_user_id, get_default_subscription_payload())
        await self.repository.add_subscription_event(clerk_user_id, "subscription_initialized", {"tier": "free"})
        return SubscriptionResponse(subscription=_normalize_subscription(seed))

    async def get_current_usage(self, clerk_user_id: str) -> SubscriptionUsageResponse:
        subscription = (await self.get_current_subscription(clerk_user_id)).subscription
        bounds = current_usage_period()
        usage_row = await self.repository.get_subscription_usage(clerk_user_id, bounds["period_key"])
        return SubscriptionUsageResponse(usage=self._build_usage(subscription, usage_row, bounds))

    async def list_history(self, clerk_user_id: str, limit: int = 50) -> SubscriptionHistoryResponse:
        rows = await self.repository.list_subscription_events(clerk_user_id, limit)
        return SubscriptionHistoryResponse(items=[SubscriptionEvent.model_validate(item) for item in rows])

    async def select_plan(self, clerk_user_id: str, payload: SelectPlanRequest) -> SubscriptionResponse:
        amount = get_plan_amount(payload.tier, payload.currency)

        row = await self.repository.upsert_subscription(
            clerk_user_id,
            {
                "tier": payload.tier,
                "status": "active",
                "currency": payload.currency,
                "amount": amount,
                "interval": "month",
                "permissions": get_tier_permissions(payload.tier),
                "limits": get_tier_limits(payload.tier),
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

        plan = next((item for item in get_plan_catalog() if item.tier == payload.tier), None)
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
        amount = get_plan_amount(tier, currency)
        status = "active" if str(getattr(session, "payment_status", "unpaid")) in {"paid", "no_payment_required"} else "incomplete"

        row = await self.repository.upsert_subscription(
            clerk_user_id,
            {
                "tier": tier,
                "status": status,
                "currency": currency,
                "amount": amount,
                "interval": "month",
                "permissions": get_tier_permissions(tier),
                "limits": get_tier_limits(tier),
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
        now_iso = _now_iso()
        demo_users = list(_load_demo_users(str(self.demo_users_file)))
        results: list[DemoUserRecord] = []

        for user in demo_users:
            user_tier = str(user.get("tier") or "pro")
            user_email = str(user.get("email") or "")
            user_name = str(user.get("name") or "Demo User")
            user_created_at = str(user.get("created_at") or now_iso)
            user_id = str(user.get("clerk_user_id") or "")
            demo_payload = get_demo_subscription_payload(user_tier if user_tier in {"free", "plus", "pro"} else "pro")

            saved_user = await self.repository.upsert_user(
                user_id,
                {
                    "email": user_email,
                    "name": user_name,
                    "permissions": demo_payload["permissions"],
                    "is_demo": True,
                    "tier": user_tier,
                    "created_at": user_created_at,
                },
            )

            await self.repository.upsert_subscription(user_id, demo_payload)
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
                    permissions=demo_payload["permissions"],
                    tier=user_tier,  # type: ignore[arg-type]
                    created_at=saved_user.get("created_at") or user_created_at,
                )
            )

        return SeedDemoUsersResponse(users=results)

    async def consume_nutrition_credits(self, clerk_user_id: str, amount: int, feature_key: str) -> SubscriptionUsageResponse:
        return await self._consume_usage(
            clerk_user_id,
            nutrition_credits=amount,
            feature_key=feature_key,
            error_message="Monthly nutrition credits exhausted",
            limit_label="nutrition_credits",
        )

    async def consume_chat_message(self, clerk_user_id: str) -> SubscriptionUsageResponse:
        return await self._consume_usage(
            clerk_user_id,
            chat_messages=1,
            feature_key="nutri_chat",
            error_message="Monthly Nutri Chat message limit reached",
            limit_label="chat_messages",
        )

    async def consume_pdf_export(self, clerk_user_id: str) -> SubscriptionUsageResponse:
        return await self._consume_usage(
            clerk_user_id,
            pdf_exports=1,
            feature_key="meal_plan_pdf_export",
            error_message="Monthly PDF export limit reached",
            limit_label="pdf_exports",
        )

    async def get_history_days(self, clerk_user_id: str) -> int | None:
        subscription = (await self.get_current_subscription(clerk_user_id)).subscription
        return subscription.limits.history_days

    async def get_max_chat_context_items(self, clerk_user_id: str) -> int:
        subscription = (await self.get_current_subscription(clerk_user_id)).subscription
        return subscription.limits.max_chat_context_items

    async def filter_history_rows(
        self,
        clerk_user_id: str,
        rows: Iterable[dict[str, Any]],
        *,
        timestamp_keys: tuple[str, ...] = ("created_at",),
    ) -> list[dict[str, Any]]:
        history_days = await self.get_history_days(clerk_user_id)
        if history_days is None:
            return list(rows)

        filtered: list[dict[str, Any]] = []
        for row in rows:
            timestamp = next((str(row.get(key, "")) for key in timestamp_keys if row.get(key)), "")
            if is_within_history_window(timestamp, history_days):
                filtered.append(row)
        return filtered

    async def can_access_history_row(
        self,
        clerk_user_id: str,
        row: dict[str, Any] | None,
        *,
        timestamp_keys: tuple[str, ...] = ("created_at",),
    ) -> bool:
        if row is None:
            return False
        filtered = await self.filter_history_rows(clerk_user_id, [row], timestamp_keys=timestamp_keys)
        return bool(filtered)

    def trim_context_payloads(self, payloads: dict[str, list[dict[str, Any]]], max_items: int) -> dict[str, list[dict[str, Any]]]:
        if max_items <= 0:
            return {key: [] for key in payloads}

        ordered_keys = [
            "calculations",
            "recommendations",
            "mealPlans",
            "recipes",
            "foodInsights",
            "ingredientChecks",
        ]
        remaining = {key: list(payloads.get(key, [])) for key in ordered_keys}
        trimmed = {key: [] for key in ordered_keys}
        taken = 0

        while taken < max_items and any(remaining.values()):
            for key in ordered_keys:
                if taken >= max_items:
                    break
                if not remaining[key]:
                    continue
                trimmed[key].append(remaining[key].pop(0))
                taken += 1

        for key, value in payloads.items():
            if key not in trimmed:
                trimmed[key] = value[:]
        return trimmed

    async def _refresh_subscription_row(self, clerk_user_id: str, row: dict[str, Any]) -> dict[str, Any]:
        tier = str(row.get("tier") or "free")
        currency = str(row.get("currency") or "USD").upper()
        expected = {
            "tier": tier,
            "status": str(row.get("status") or "active"),
            "currency": currency,
            "amount": float(get_plan_amount(tier, currency)),
            "interval": str(row.get("interval") or "month"),
            "permissions": get_tier_permissions(tier),
            "limits": get_tier_limits(tier),
            "is_demo": bool(row.get("is_demo", False)),
            "stripe_customer_id": row.get("stripe_customer_id"),
            "stripe_subscription_id": row.get("stripe_subscription_id"),
            "stripe_checkout_session_id": row.get("stripe_checkout_session_id"),
        }

        if self._subscription_needs_refresh(row, expected):
            return await self.repository.upsert_subscription(clerk_user_id, expected)
        return row

    @staticmethod
    def _subscription_needs_refresh(row: dict[str, Any] | None, expected_payload: dict[str, Any]) -> bool:
        if not row:
            return True
        permissions = row.get("permissions", {})
        limits = row.get("limits", {})
        if not isinstance(permissions, dict) or permissions != expected_payload.get("permissions", {}):
            return True
        if not isinstance(limits, dict) or limits != expected_payload.get("limits", {}):
            return True
        for key in ("tier", "status", "currency", "interval", "is_demo"):
            if row.get(key) != expected_payload.get(key):
                return True
        if float(row.get("amount") or 0) != float(expected_payload.get("amount") or 0):
            return True
        return False

    @staticmethod
    def _default_usage_payload(bounds: dict[str, str]) -> dict[str, Any]:
        return {
            "period_start": bounds["period_start"],
            "period_end": bounds["period_end"],
            "nutrition_credits_used": 0,
            "chat_messages_used": 0,
            "pdf_exports_used": 0,
            "feature_breakdown": {},
        }

    def _build_usage(
        self,
        subscription: SubscriptionRecord,
        usage_row: dict[str, Any] | None,
        bounds: dict[str, str],
    ) -> SubscriptionUsage:
        payload = self._default_usage_payload(bounds)
        if usage_row:
            payload.update(usage_row)

        limits = subscription.limits
        nutrition_used = int(payload.get("nutrition_credits_used") or 0)
        chat_used = int(payload.get("chat_messages_used") or 0)
        pdf_used = int(payload.get("pdf_exports_used") or 0)

        return SubscriptionUsage(
            clerk_user_id=subscription.clerk_user_id,
            tier=subscription.tier,
            period=SubscriptionUsagePeriod.model_validate(bounds),
            nutrition_credits=self._allowance(nutrition_used, limits.monthly_nutrition_credits),
            chat_messages=self._allowance(chat_used, limits.monthly_chat_messages),
            pdf_exports=self._allowance(pdf_used, limits.pdf_exports_per_month),
            feature_breakdown={
                key: int(value)
                for key, value in dict(payload.get("feature_breakdown") or {}).items()
                if isinstance(value, (int, float))
            },
        )

    @staticmethod
    def _allowance(used: int, limit: int | None) -> UsageAllowance:
        remaining = None if limit is None else max(limit - used, 0)
        return UsageAllowance(used=used, limit=limit, remaining=remaining)

    async def _consume_usage(
        self,
        clerk_user_id: str,
        *,
        nutrition_credits: int = 0,
        chat_messages: int = 0,
        pdf_exports: int = 0,
        feature_key: str,
        error_message: str,
        limit_label: str,
    ) -> SubscriptionUsageResponse:
        subscription = (await self.get_current_subscription(clerk_user_id)).subscription
        bounds = current_usage_period()
        try:
            saved = await self.repository.increment_subscription_usage(
                clerk_user_id,
                bounds["period_key"],
                {
                    "bounds": bounds,
                    "deltas": {
                        "nutrition_credits_used": nutrition_credits,
                        "chat_messages_used": chat_messages,
                        "pdf_exports_used": pdf_exports,
                    },
                    "limits": {
                        "monthly_nutrition_credits": subscription.limits.monthly_nutrition_credits,
                        "monthly_chat_messages": subscription.limits.monthly_chat_messages,
                        "pdf_exports_per_month": subscription.limits.pdf_exports_per_month,
                    },
                    "feature_key": feature_key,
                },
            )
        except Exception as exc:
            if isinstance(exc, AppException) and exc.code == "SUBSCRIPTION_LIMIT_REACHED":
                raise AppException(
                    "SUBSCRIPTION_LIMIT_REACHED",
                    error_message,
                    status_code=403,
                    details={
                        "limit_type": limit_label,
                        "suggested_action": "Upgrade your subscription plan",
                    },
                ) from exc
            reason = str(exc).lower()
            if "limit_reached" in reason:
                raise AppException(
                    "SUBSCRIPTION_LIMIT_REACHED",
                    error_message,
                    status_code=403,
                    details={
                        "limit_type": limit_label,
                        "suggested_action": "Upgrade your subscription plan",
                    },
                ) from exc
            raise

        return SubscriptionUsageResponse(usage=self._build_usage(subscription, saved, bounds))
