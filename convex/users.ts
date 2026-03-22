import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const upsert = mutation({
  args: {
    clerk_user_id: v.string(),
    email: v.optional(v.string()),
    name: v.optional(v.string()),
    image_url: v.optional(v.string()),
    permissions: v.optional(v.any()),
    is_demo: v.optional(v.boolean()),
    tier: v.optional(v.string()),
    created_at: v.optional(v.string()),
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
        permissions: args.permissions,
        is_demo: args.is_demo,
        tier: args.tier,
      });
      return { ...existing, ...args };
    }

    const now = args.created_at ?? new Date().toISOString();
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

export const seedDemoUsers = mutation({
  args: { users: v.array(v.any()) },
  handler: async (ctx, args) => {
    const created = [];
    for (const row of args.users) {
      const existing = await ctx.db
        .query("users")
        .withIndex("by_clerk_user_id", (q) => q.eq("clerk_user_id", row.clerk_user_id))
        .first();

      const payload = {
        clerk_user_id: String(row.clerk_user_id),
        email: typeof row.email === "string" ? row.email : undefined,
        name: typeof row.name === "string" ? row.name : undefined,
        permissions: row.permissions ?? {},
        is_demo: true,
        tier: typeof row.tier === "string" ? row.tier : "pro",
        created_at: typeof row.created_at === "string" ? row.created_at : new Date().toISOString(),
      };

      if (existing) {
        await ctx.db.patch(existing._id, payload);
      } else {
        await ctx.db.insert("users", payload);
      }

      created.push(payload);
    }
    return created;
  },
});
