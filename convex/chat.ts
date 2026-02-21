import { mutation, query, action } from "./_generated/server";
import { v } from "convex/values";

const makeId = () => `${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;

export const createSession = mutation({
  args: { clerk_user_id: v.string(), title: v.string() },
  handler: async (ctx, args) => {
    const now = new Date().toISOString();
    const session_id = makeId();
    const doc = {
      session_id,
      clerk_user_id: args.clerk_user_id,
      title: args.title,
      created_at: now,
      last_message_at: now,
    };
    await ctx.db.insert("chatSessions", doc);
    return doc;
  },
});

export const listSessions = query({
  args: { clerk_user_id: v.string(), limit: v.number() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("chatSessions")
      .withIndex("by_user_created", (q) => q.eq("clerk_user_id", args.clerk_user_id))
      .order("desc")
      .take(args.limit);
  },
});

export const addMessage = mutation({
  args: {
    clerk_user_id: v.string(),
    session_id: v.string(),
    role: v.string(),
    content: v.string(),
  },
  handler: async (ctx, args) => {
    const now = new Date().toISOString();
    const message_id = makeId();

    const session = await ctx.db
      .query("chatSessions")
      .withIndex("by_user_session", (q) => q.eq("clerk_user_id", args.clerk_user_id).eq("session_id", args.session_id))
      .first();

    if (!session) throw new Error("session not found");

    const doc = {
      message_id,
      session_id: args.session_id,
      clerk_user_id: args.clerk_user_id,
      role: args.role,
      content: args.content,
      created_at: now,
    };

    await ctx.db.insert("chatMessages", doc);
    await ctx.db.patch(session._id, { last_message_at: now });

    return doc;
  },
});

export const listMessages = query({
  args: { clerk_user_id: v.string(), session_id: v.string(), limit: v.number() },
  handler: async (ctx, args) => {
    const rows = await ctx.db
      .query("chatMessages")
      .withIndex("by_user_session_created", (q) =>
        q.eq("clerk_user_id", args.clerk_user_id).eq("session_id", args.session_id)
      )
      .order("desc")
      .take(args.limit);

    return rows.reverse();
  },
});

export const totalMessages = action({
  args: { clerk_user_id: v.string() },
  handler: async (ctx, args) => {
    const sessions = await ctx.runQuery("chat:listSessions" as any, {
      clerk_user_id: args.clerk_user_id,
      limit: 100,
    });

    let total = 0;
    for (const session of sessions) {
      const messages = await ctx.runQuery("chat:listMessages" as any, {
        clerk_user_id: args.clerk_user_id,
        session_id: session.session_id,
        limit: 1000,
      });
      total += messages.length;
    }
    return total;
  },
});
