import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const upsert = mutation({
  args: {
    clerk_user_id: v.string(),
    email: v.optional(v.string()),
    name: v.optional(v.string()),
    image_url: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("users")
      .withIndex("by_clerk_user_id", (q) => q.eq("clerk_user_id", args.clerk_user_id))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        email: args.email,
        name: args.name,
        image_url: args.image_url,
      });
      return { ...existing, ...args };
    }

    const now = new Date().toISOString();
    const id = await ctx.db.insert("users", { ...args, created_at: now });
    return { id, ...args, created_at: now };
  },
});

export const getByClerkUserId = query({
  args: { clerk_user_id: v.string() },
  handler: async (ctx, args) => {
    const row = await ctx.db
      .query("users")
      .withIndex("by_clerk_user_id", (q) => q.eq("clerk_user_id", args.clerk_user_id))
      .first();
    if (!row) return null;
    const { _id, _creationTime, ...rest } = row;
    return { id: _id, ...rest };
  },
});
