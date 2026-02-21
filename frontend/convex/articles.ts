import { mutation, query, action } from "./_generated/server";
import { v } from "convex/values";

export const seed = mutation({
  args: { items: v.array(v.any()) },
  handler: async (ctx, args) => {
    let inserted = 0;
    for (const item of args.items) {
      if (!item.slug) continue;
      const exists = await ctx.db
        .query("articles")
        .withIndex("by_slug", (q) => q.eq("slug", item.slug))
        .first();
      if (exists) continue;

      await ctx.db.insert("articles", {
        slug: item.slug,
        title: item.title,
        summary: item.summary,
        content: item.content,
        created_at: item.created_at ?? new Date().toISOString(),
      });
      inserted += 1;
    }
    return inserted;
  },
});

export const list = query({
  args: { query_text: v.optional(v.string()), limit: v.number() },
  handler: async (ctx, args) => {
    const rows = await ctx.db.query("articles").withIndex("by_created").order("desc").take(args.limit);
    if (!args.query_text) return rows;

    const q = args.query_text.toLowerCase();
    return rows.filter(
      (row) => row.title.toLowerCase().includes(q) || row.summary.toLowerCase().includes(q)
    );
  },
});

export const getBySlug = query({
  args: { slug: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db.query("articles").withIndex("by_slug", (q) => q.eq("slug", args.slug)).first();
  },
});

export const count = action({
  args: {},
  handler: async (ctx) => {
    const rows = await ctx.runQuery("articles:list" as any, { query_text: undefined, limit: 1000 });
    return rows.length;
  },
});
