import { mutation, query, action } from "./_generated/server";
import { v } from "convex/values";

const makeId = () => `${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;

export const create = mutation({
  args: { clerk_user_id: v.string(), payload: v.any() },
  handler: async (ctx, args) => {
    const record_id = makeId();
    const doc = {
      record_id,
      clerk_user_id: args.clerk_user_id,
      operation_id: typeof args.payload.operation_id === "string" ? args.payload.operation_id : undefined,
      idempotency_key: typeof args.payload.idempotency_key === "string" ? args.payload.idempotency_key : undefined,
      calculator_type: args.payload.calculator_type,
      payload: args.payload.payload,
      result: args.payload.result,
      created_at: args.payload.created_at ?? new Date().toISOString(),
    };
    await ctx.db.insert("calculations", doc);
    return { id: record_id, ...doc };
  },
});

export const listByUser = query({
  args: { clerk_user_id: v.string(), limit: v.number() },
  handler: async (ctx, args) => {
    const rows = await ctx.db
      .query("calculations")
      .withIndex("by_user_created", (q) => q.eq("clerk_user_id", args.clerk_user_id))
      .order("desc")
      .take(args.limit);

    return rows.map(({ _id, _creationTime, record_id, ...rest }) => ({ id: record_id, ...rest }));
  },
});

export const aggregateCount = action({
  args: { clerk_user_id: v.string() },
  handler: async (ctx, args) => {
    const rows = await ctx.runQuery("calculations:listByUser" as any, {
      clerk_user_id: args.clerk_user_id,
      limit: 1000,
    });
    return rows.length;
  },
});
