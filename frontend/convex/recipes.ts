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
      created_at,
      input: args.payload.input ?? {},
      recipe_name: args.payload.recipe_name ?? "Generated Recipe",
      ingredients: args.payload.ingredients ?? [],
      steps: args.payload.steps ?? [],
      ingredient_list: args.payload.ingredient_list ?? [],
      explanation:
      typeof args.payload.explanation === "string" ? args.payload.explanation : undefined,
      raw_response: args.payload.raw_response ?? "",
    };
    await ctx.db.insert("recipes", doc);
    return { id: record_id, ...doc };
  },
});

export const listByUser = query({
  args: { clerk_user_id: v.string(), limit: v.number() },
  handler: async (ctx, args) => {
    const rows = await ctx.db
      .query("recipes")
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
      .query("recipes")
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
    const rows = await ctx.runQuery("recipes:listByUser" as any, {
      clerk_user_id: args.clerk_user_id,
      limit: 1000,
    });
    return rows.length;
  },
});
