import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

const makeId = () => `${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;

export const upsert = mutation({
  args: { clerk_user_id: v.string(), payload: v.any() },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("subscriptions")
      .withIndex("by_user", (q) => q.eq("clerk_user_id", args.clerk_user_id))
      .first();

    const now = new Date().toISOString();
    const base = {
      subscription_id: existing?.subscription_id ?? makeId(),
      clerk_user_id: args.clerk_user_id,
      tier: typeof args.payload.tier === "string" ? args.payload.tier : "free",
      status: typeof args.payload.status === "string" ? args.payload.status : "active",
      currency: typeof args.payload.currency === "string" ? args.payload.currency : "USD",
      amount: typeof args.payload.amount === "number" ? args.payload.amount : 0,
      interval: typeof args.payload.interval === "string" ? args.payload.interval : "month",
      permissions: args.payload.permissions ?? {},
      is_demo: typeof args.payload.is_demo === "boolean" ? args.payload.is_demo : false,
      stripe_customer_id:
        typeof args.payload.stripe_customer_id === "string" ? args.payload.stripe_customer_id : undefined,
      stripe_subscription_id:
        typeof args.payload.stripe_subscription_id === "string" ? args.payload.stripe_subscription_id : undefined,
      stripe_checkout_session_id:
        typeof args.payload.stripe_checkout_session_id === "string"
          ? args.payload.stripe_checkout_session_id
          : undefined,
      created_at: existing?.created_at ?? (typeof args.payload.created_at === "string" ? args.payload.created_at : now),
      updated_at: now,
    };

    if (existing) {
      await ctx.db.patch(existing._id, base);
      const { _id, _creationTime, ...rest } = { ...existing, ...base };
      return rest;
    }

    await ctx.db.insert("subscriptions", base);
    return base;
  },
});

export const getByUser = query({
  args: { clerk_user_id: v.string() },
  handler: async (ctx, args) => {
    const row = await ctx.db
      .query("subscriptions")
      .withIndex("by_user", (q) => q.eq("clerk_user_id", args.clerk_user_id))
      .first();

    if (!row) return null;
    const { _id, _creationTime, ...rest } = row;
    return rest;
  },
});

export const addEvent = mutation({
  args: { clerk_user_id: v.string(), event_type: v.string(), payload: v.any() },
  handler: async (ctx, args) => {
    const event = {
      event_id: makeId(),
      clerk_user_id: args.clerk_user_id,
      event_type: args.event_type,
      payload: args.payload ?? {},
      created_at: new Date().toISOString(),
    };

    await ctx.db.insert("subscriptionEvents", event);
    return { id: event.event_id, ...event };
  },
});

export const listEvents = query({
  args: { clerk_user_id: v.string(), limit: v.number() },
  handler: async (ctx, args) => {
    const rows = await ctx.db
      .query("subscriptionEvents")
      .withIndex("by_user_created", (q) => q.eq("clerk_user_id", args.clerk_user_id))
      .order("desc")
      .take(args.limit);

    return rows.map(({ _id, _creationTime, event_id, ...rest }) => ({ id: event_id, ...rest }));
  },
});

export const getUsageByUserPeriod = query({
  args: { clerk_user_id: v.string(), period_key: v.string() },
  handler: async (ctx, args) => {
    const row = await ctx.db
      .query("subscriptionUsage")
      .withIndex("by_user_period", (q) => q.eq("clerk_user_id", args.clerk_user_id).eq("period_key", args.period_key))
      .first();

    if (!row) return null;
    const { _id, _creationTime, ...rest } = row;
    return rest;
  },
});

export const upsertUsage = mutation({
  args: { clerk_user_id: v.string(), period_key: v.string(), payload: v.any() },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("subscriptionUsage")
      .withIndex("by_user_period", (q) => q.eq("clerk_user_id", args.clerk_user_id).eq("period_key", args.period_key))
      .first();

    const now = new Date().toISOString();
    const base = {
      usage_id: existing?.usage_id ?? makeId(),
      clerk_user_id: args.clerk_user_id,
      period_key: args.period_key,
      period_start: typeof args.payload.period_start === "string" ? args.payload.period_start : now,
      period_end: typeof args.payload.period_end === "string" ? args.payload.period_end : now,
      nutrition_credits_used:
        typeof args.payload.nutrition_credits_used === "number" ? args.payload.nutrition_credits_used : 0,
      chat_messages_used: typeof args.payload.chat_messages_used === "number" ? args.payload.chat_messages_used : 0,
      pdf_exports_used: typeof args.payload.pdf_exports_used === "number" ? args.payload.pdf_exports_used : 0,
      feature_breakdown: args.payload.feature_breakdown ?? {},
      created_at: existing?.created_at ?? (typeof args.payload.created_at === "string" ? args.payload.created_at : now),
      updated_at: now,
    };

    if (existing) {
      await ctx.db.patch(existing._id, base);
      const { _id, _creationTime, ...rest } = { ...existing, ...base };
      return rest;
    }

    await ctx.db.insert("subscriptionUsage", base);
    return base;
  },
});

export const incrementUsage = mutation({
  args: { clerk_user_id: v.string(), period_key: v.string(), payload: v.any() },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("subscriptionUsage")
      .withIndex("by_user_period", (q) => q.eq("clerk_user_id", args.clerk_user_id).eq("period_key", args.period_key))
      .first();

    const now = new Date().toISOString();
    const bounds = args.payload.bounds ?? {};
    const deltas = args.payload.deltas ?? {};
    const limits = args.payload.limits ?? {};
    const currentNutrition = Number(existing?.nutrition_credits_used ?? 0);
    const currentChat = Number(existing?.chat_messages_used ?? 0);
    const currentPdf = Number(existing?.pdf_exports_used ?? 0);
    const nextNutrition = currentNutrition + Number(deltas.nutrition_credits_used ?? 0);
    const nextChat = currentChat + Number(deltas.chat_messages_used ?? 0);
    const nextPdf = currentPdf + Number(deltas.pdf_exports_used ?? 0);

    if (limits.monthly_nutrition_credits !== undefined && limits.monthly_nutrition_credits !== null) {
      if (nextNutrition > Number(limits.monthly_nutrition_credits)) throw new Error("nutrition_limit_reached");
    }
    if (limits.monthly_chat_messages !== undefined && limits.monthly_chat_messages !== null) {
      if (nextChat > Number(limits.monthly_chat_messages)) throw new Error("chat_limit_reached");
    }
    if (limits.pdf_exports_per_month !== undefined && limits.pdf_exports_per_month !== null) {
      if (nextPdf > Number(limits.pdf_exports_per_month)) throw new Error("pdf_limit_reached");
    }

    const featureKey = String(args.payload.feature_key ?? "unknown");
    const featureBreakdown = { ...(existing?.feature_breakdown ?? {}) } as Record<string, number>;
    featureBreakdown[featureKey] = Number(featureBreakdown[featureKey] ?? 0) + 1;

    const base = {
      usage_id: existing?.usage_id ?? makeId(),
      clerk_user_id: args.clerk_user_id,
      period_key: args.period_key,
      period_start: typeof bounds.period_start === "string" ? bounds.period_start : now,
      period_end: typeof bounds.period_end === "string" ? bounds.period_end : now,
      nutrition_credits_used: nextNutrition,
      chat_messages_used: nextChat,
      pdf_exports_used: nextPdf,
      feature_breakdown: featureBreakdown,
      created_at: existing?.created_at ?? now,
      updated_at: now,
    };

    if (existing) {
      await ctx.db.patch(existing._id, base);
      const { _id, _creationTime, ...rest } = { ...existing, ...base };
      return rest;
    }

    await ctx.db.insert("subscriptionUsage", base);
    return base;
  },
});
