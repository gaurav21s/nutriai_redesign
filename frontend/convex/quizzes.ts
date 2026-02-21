import { mutation, query, action } from "./_generated/server";
import { v } from "convex/values";

const makeId = () => `${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;

export const createSession = mutation({
  args: { clerk_user_id: v.string(), payload: v.any() },
  handler: async (ctx, args) => {
    const session_id = makeId();
    const created_at = args.payload.created_at ?? new Date().toISOString();
    const doc = {
      session_id,
      clerk_user_id: args.clerk_user_id,
      topic: args.payload.topic,
      difficulty: args.payload.difficulty,
      questions: args.payload.questions ?? [],
      raw_response: args.payload.raw_response,
      created_at,
    };
    await ctx.db.insert("quizSessions", doc);
    return doc;
  },
});

export const getSession = query({
  args: { clerk_user_id: v.string(), session_id: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("quizSessions")
      .withIndex("by_user_session", (q) => q.eq("clerk_user_id", args.clerk_user_id).eq("session_id", args.session_id))
      .first();
  },
});

export const createSubmission = mutation({
  args: { clerk_user_id: v.string(), session_id: v.string(), payload: v.any() },
  handler: async (ctx, args) => {
    const attempt_id = makeId();
    const created_at = new Date().toISOString();
    const doc = {
      attempt_id,
      session_id: args.session_id,
      clerk_user_id: args.clerk_user_id,
      total_questions: args.payload.total_questions,
      correct_answers: args.payload.correct_answers,
      score_percentage: args.payload.score_percentage,
      results: args.payload.results ?? [],
      created_at,
    };
    await ctx.db.insert("quizAttempts", doc);
    return doc;
  },
});

export const listHistory = query({
  args: { clerk_user_id: v.string(), limit: v.number() },
  handler: async (ctx, args) => {
    const sessions = await ctx.db
      .query("quizSessions")
      .withIndex("by_user_created", (q) => q.eq("clerk_user_id", args.clerk_user_id))
      .order("desc")
      .take(args.limit);

    const results = [] as Array<Record<string, unknown>>;
    for (const session of sessions) {
      const latestAttempt = await ctx.db
        .query("quizAttempts")
        .withIndex("by_user_session", (q) => q.eq("clerk_user_id", args.clerk_user_id).eq("session_id", session.session_id))
        .order("desc")
        .first();

      results.push({
        session_id: session.session_id,
        topic: session.topic,
        difficulty: session.difficulty,
        created_at: session.created_at,
        score_percentage: latestAttempt?.score_percentage,
      });
    }

    return results;
  },
});

export const aggregateScore = action({
  args: { clerk_user_id: v.string() },
  handler: async (ctx, args) => {
    const rows = await ctx.runQuery("quizzes:listHistory" as any, {
      clerk_user_id: args.clerk_user_id,
      limit: 100,
    });

    if (!rows.length) return 0;
    const score = rows.reduce((acc: number, row: any) => acc + (row.score_percentage ?? 0), 0);
    return score / rows.length;
  },
});
