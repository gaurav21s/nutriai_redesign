import { mutation, query, action } from "./_generated/server";
import { v } from "convex/values";

const makeId = () => `${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;

export const create = mutation({
  args: { clerk_user_id: v.string(), payload: v.any() },
  handler: async (ctx, args) => {
    const record_id = makeId();
    const created_at = args.payload.created_at ?? new Date().toISOString();
    const doc = {
      record_id,
      clerk_user_id: args.clerk_user_id,
      operation_id: typeof args.payload.operation_id === "string" ? args.payload.operation_id : undefined,
      meal_plan_record_id: String(args.payload.meal_plan_record_id ?? ""),
      full_name: String(args.payload.full_name ?? ""),
      age: Number(args.payload.age ?? 0),
      file_name: String(args.payload.file_name ?? "meal_plan.pdf"),
      mime_type: String(args.payload.mime_type ?? "application/pdf"),
      byte_size: Number(args.payload.byte_size ?? 0),
      pdf_base64: String(args.payload.pdf_base64 ?? ""),
      created_at,
    };
    await ctx.db.insert("mealPlanPdfExports", doc);
    return { id: record_id, ...doc };
  },
});

export const listByUser = query({
  args: { clerk_user_id: v.string(), limit: v.number() },
  handler: async (ctx, args) => {
    const rows = await ctx.db
      .query("mealPlanPdfExports")
      .withIndex("by_user_created", (q) => q.eq("clerk_user_id", args.clerk_user_id))
      .order("desc")
      .take(args.limit);

    return rows.map(({ _id, _creationTime, record_id, ...rest }) => ({ id: record_id, ...rest }));
  },
});

export const getById = query({
  args: { clerk_user_id: v.string(), record_id: v.string() },
  handler: async (ctx, args) => {
    const row = await ctx.db
      .query("mealPlanPdfExports")
      .withIndex("by_user_record", (q) => q.eq("clerk_user_id", args.clerk_user_id).eq("record_id", args.record_id))
      .first();

    if (!row) return null;
    const { _id, _creationTime, record_id, ...rest } = row;
    return { id: record_id, ...rest };
  },
});

export const aggregateCount = action({
  args: { clerk_user_id: v.string() },
  handler: async (ctx, args) => {
    const rows = await ctx.runQuery("mealPlanPdfExports:listByUser" as any, {
      clerk_user_id: args.clerk_user_id,
      limit: 1000,
    });
    return rows.length;
  },
});
