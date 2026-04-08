import { mutation, query, action } from "./_generated/server";
import { v } from "convex/values";

const makeId = () => crypto.randomUUID().replace(/-/g, "");

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
      next_sequence_no: 0,
    };
    await ctx.db.insert("chatSessions", doc);
    return doc;
  },
});

export const updateSession = mutation({
  args: { clerk_user_id: v.string(), session_id: v.string(), payload: v.any() },
  handler: async (ctx, args) => {
    const session = await ctx.db
      .query("chatSessions")
      .withIndex("by_user_session", (q) => q.eq("clerk_user_id", args.clerk_user_id).eq("session_id", args.session_id))
      .first();
    if (!session) return null;
    const patch: Record<string, unknown> = {};
    if (typeof args.payload.title === "string") patch.title = args.payload.title;
    if (typeof args.payload.last_message_at === "string") patch.last_message_at = args.payload.last_message_at;
    await ctx.db.patch(session._id, patch);
    const { _id, _creationTime, ...rest } = { ...session, ...patch };
    return rest;
  },
});

export const deleteSession = mutation({
  args: { clerk_user_id: v.string(), session_id: v.string() },
  handler: async (ctx, args) => {
    const session = await ctx.db
      .query("chatSessions")
      .withIndex("by_user_session", (q) => q.eq("clerk_user_id", args.clerk_user_id).eq("session_id", args.session_id))
      .first();
    if (!session) return null;

    const messages = await ctx.db
      .query("chatMessages")
      .withIndex("by_user_session_created", (q) =>
        q.eq("clerk_user_id", args.clerk_user_id).eq("session_id", args.session_id)
      )
      .collect();
    for (const message of messages) {
      await ctx.db.delete(message._id);
    }

    const actions = await ctx.db
      .query("chatActions")
      .withIndex("by_user_session_created", (q) =>
        q.eq("clerk_user_id", args.clerk_user_id).eq("session_id", args.session_id)
      )
      .collect();
    for (const action of actions) {
      await ctx.db.delete(action._id);
    }

    await ctx.db.delete(session._id);
    return { session_id: args.session_id, deleted: true };
  },
});

export const getSession = query({
  args: { clerk_user_id: v.string(), session_id: v.string() },
  handler: async (ctx, args) => {
    const session = await ctx.db
      .query("chatSessions")
      .withIndex("by_user_session", (q) => q.eq("clerk_user_id", args.clerk_user_id).eq("session_id", args.session_id))
      .first();

    if (!session) return null;
    const { _id, _creationTime, ...rest } = session;
    return rest;
  },
});

export const reserveSequence = mutation({
  args: { clerk_user_id: v.string(), session_id: v.string() },
  handler: async (ctx, args) => {
    const session = await ctx.db
      .query("chatSessions")
      .withIndex("by_user_session", (q) => q.eq("clerk_user_id", args.clerk_user_id).eq("session_id", args.session_id))
      .first();
    if (!session) throw new Error("session not found");
    const sequence_no = Number(session.next_sequence_no ?? 0) + 1;
    await ctx.db.patch(session._id, { next_sequence_no: sequence_no });
    return { sequence_no };
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
    metadata: v.optional(v.any()),
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
      operation_id: typeof args.metadata?.operation_id === "string" ? args.metadata.operation_id : undefined,
      sequence_no: typeof args.metadata?.sequence_no === "number" ? args.metadata.sequence_no : undefined,
      role: args.role,
      content: args.content,
      metadata: args.metadata,
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

export const createAction = mutation({
  args: {
    clerk_user_id: v.string(),
    session_id: v.string(),
    payload: v.any(),
  },
  handler: async (ctx, args) => {
    const now = new Date().toISOString();
    const action_id = makeId();
    const doc = {
      action_id,
      session_id: args.session_id,
      clerk_user_id: args.clerk_user_id,
      kind: String(args.payload.kind ?? ""),
      title: String(args.payload.title ?? ""),
      summary: String(args.payload.summary ?? ""),
      status: String(args.payload.status ?? "pending"),
      preview_payload: args.payload.preview_payload ?? {},
      created_at: now,
      resolved_at: undefined,
      saved_record_id: undefined,
    };
    await ctx.db.insert("chatActions", doc);
    return doc;
  },
});

export const getAction = query({
  args: { clerk_user_id: v.string(), session_id: v.string(), action_id: v.string() },
  handler: async (ctx, args) => {
    const row = await ctx.db
      .query("chatActions")
      .withIndex("by_user_session_action", (q) =>
        q.eq("clerk_user_id", args.clerk_user_id).eq("session_id", args.session_id).eq("action_id", args.action_id)
      )
      .first();

    if (!row) return null;
    const { _id, _creationTime, ...rest } = row;
    return rest;
  },
});

export const updateAction = mutation({
  args: {
    clerk_user_id: v.string(),
    session_id: v.string(),
    action_id: v.string(),
    payload: v.any(),
  },
  handler: async (ctx, args) => {
    const row = await ctx.db
      .query("chatActions")
      .withIndex("by_user_session_action", (q) =>
        q.eq("clerk_user_id", args.clerk_user_id).eq("session_id", args.session_id).eq("action_id", args.action_id)
      )
      .first();

    if (!row) return null;

    const patch: Record<string, unknown> = {};
    if (args.payload.status !== undefined) patch.status = String(args.payload.status);
    if (args.payload.saved_record_id !== undefined) patch.saved_record_id = args.payload.saved_record_id;
    if (patch.status && !row.resolved_at && String(patch.status) !== "pending") {
      patch.resolved_at = new Date().toISOString();
    }
    await ctx.db.patch(row._id, patch);
    const updated = { ...row, ...patch };
    const { _id, _creationTime, ...rest } = updated;
    return rest;
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
