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
