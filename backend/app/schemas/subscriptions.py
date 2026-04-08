"""Billing and subscription schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


CurrencyCode = Literal["USD", "INR"]
PlanTier = Literal["free", "plus", "pro"]
SubscriptionStatus = Literal["active", "trialing", "canceled", "incomplete", "unpaid"]


class PlanPrice(BaseModel):
    currency: CurrencyCode
    amount: float = Field(..., ge=0)
    interval: Literal["month"] = "month"


class PlanLimits(BaseModel):
    monthly_nutrition_credits: int = Field(..., ge=0)
    monthly_chat_messages: int = Field(..., ge=0)
    history_days: int | None = Field(default=None, ge=1)
    pdf_exports_per_month: int = Field(..., ge=0)
    max_chat_context_items: int = Field(..., ge=0)
    priority_processing: bool = False


class PlanSummary(BaseModel):
    tier: PlanTier
    label: str
    description: str
    recommended: bool = False
    features: list[str]
    limits: PlanLimits
    price_usd: PlanPrice
    price_inr: PlanPrice


class PricingCatalogResponse(BaseModel):
    plans: list[PlanSummary]
    stripe_publishable_key: str | None = None


class SubscriptionRecord(BaseModel):
    clerk_user_id: str
    tier: PlanTier
    status: SubscriptionStatus
    currency: CurrencyCode
    amount: float = Field(..., ge=0)
    interval: Literal["month"] = "month"
    permissions: dict[str, bool]
    limits: PlanLimits
    is_demo: bool = False
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    stripe_checkout_session_id: str | None = None
    created_at: datetime
    updated_at: datetime


class SubscriptionResponse(BaseModel):
    subscription: SubscriptionRecord


class SubscriptionEvent(BaseModel):
    id: str
    clerk_user_id: str
    event_type: str
    payload: dict
    created_at: datetime


class SubscriptionHistoryResponse(BaseModel):
    items: list[SubscriptionEvent]


class UsageAllowance(BaseModel):
    used: int = Field(..., ge=0)
    limit: int | None = Field(default=None, ge=0)
    remaining: int | None = Field(default=None, ge=0)


class SubscriptionUsagePeriod(BaseModel):
    period_key: str
    period_start: datetime
    period_end: datetime
    next_reset_at: datetime


class SubscriptionUsage(BaseModel):
    clerk_user_id: str
    tier: PlanTier
    period: SubscriptionUsagePeriod
    nutrition_credits: UsageAllowance
    chat_messages: UsageAllowance
    pdf_exports: UsageAllowance
    feature_breakdown: dict[str, int]


class SubscriptionUsageResponse(BaseModel):
    usage: SubscriptionUsage


class SelectPlanRequest(BaseModel):
    tier: PlanTier
    currency: CurrencyCode = "USD"


class CreateCheckoutSessionRequest(BaseModel):
    tier: Literal["plus", "pro"]
    currency: CurrencyCode
    success_url: str
    cancel_url: str


class CreateCheckoutSessionResponse(BaseModel):
    session_id: str
    checkout_url: str


class ConfirmCheckoutRequest(BaseModel):
    session_id: str


class DemoUserRecord(BaseModel):
    clerk_user_id: str
    email: str
    name: str
    permissions: dict[str, bool]
    tier: PlanTier
    created_at: datetime


class SeedDemoUsersResponse(BaseModel):
    users: list[DemoUserRecord]
