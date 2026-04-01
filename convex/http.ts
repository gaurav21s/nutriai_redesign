import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";

const http = httpRouter();

type FeatureName =
  | "foodInsights"
  | "ingredientChecks"
  | "mealPlans"
  | "recipes"
  | "calculations"
  | "recommendations";

const featureFunctions: Record<
  FeatureName,
  {
    create: string;
    list: string;
    get?: string;
  }
> = {
  foodInsights: {
    create: "foodInsights:create",
    list: "foodInsights:listByUser",
    get: "foodInsights:getById",
  },
  ingredientChecks: {
    create: "ingredientChecks:create",
    list: "ingredientChecks:listByUser",
    get: "ingredientChecks:getById",
  },
  mealPlans: {
    create: "mealPlans:create",
    list: "mealPlans:listByUser",
    get: "mealPlans:getById",
  },
  recipes: {
    create: "recipes:create",
    list: "recipes:listByUser",
    get: "recipes:getById",
  },
  calculations: {
    create: "calculations:create",
    list: "calculations:listByUser",
  },
  recommendations: {
    create: "recommendations:create",
    list: "recommendations:listByUser",
    get: "recommendations:getById",
  },
};

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function normalizeChatSession(row: Record<string, unknown>) {
  const { _id, _creationTime, ...rest } = row;
  return rest;
}

function normalizeChatMessage(row: Record<string, unknown>) {
  const { _id, _creationTime, message_id, ...rest } = row;
  return { id: String(message_id ?? ""), ...rest };
}

function normalizeChatAction(row: Record<string, unknown>) {
  const { _id, _creationTime, ...rest } = row;
  return rest;
}

function normalizeArticle(row: Record<string, unknown>) {
  const { _id, _creationTime, ...rest } = row;
  return { id: String(_id ?? ""), ...rest };
}

function normalizeSubscription(row: Record<string, unknown>) {
  const { _id, _creationTime, ...rest } = row;
  return rest;
}

function ensureBackendSecret(req: Request): boolean {
  const expected = process.env.BACKEND_CONVEX_SHARED_SECRET;
  if (!expected) return true;
  const provided = req.headers.get("x-backend-secret");
  return provided === expected;
}

http.route({
  path: "/backend/records/create",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const body = (await req.json()) as {
      feature: FeatureName;
      clerkUserId: string;
      payload: Record<string, unknown>;
    };

    const feature = featureFunctions[body.feature];
    if (!feature) return json({ ok: false, error: "invalid feature" }, 400);

    const created = await ctx.runMutation(feature.create as any, {
      clerk_user_id: body.clerkUserId,
      payload: body.payload ?? {},
    });

    return json({ ok: true, data: created });
  }),
});

http.route({
  path: "/backend/records/list",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const body = (await req.json()) as {
      feature: FeatureName;
      clerkUserId: string;
      limit?: number;
    };

    const feature = featureFunctions[body.feature];
    if (!feature) return json({ ok: false, error: "invalid feature" }, 400);

    const items = await ctx.runQuery(feature.list as any, {
      clerk_user_id: body.clerkUserId,
      limit: Math.min(Math.max(body.limit ?? 20, 1), 100),
    });

    return json({ ok: true, data: { items } });
  }),
});

http.route({
  path: "/backend/records/get",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const body = (await req.json()) as {
      feature: FeatureName;
      clerkUserId: string;
      recordId: string;
    };

    const feature = featureFunctions[body.feature];
    if (!feature) return json({ ok: false, error: "invalid feature" }, 400);

    if (feature.get) {
      const row = await ctx.runQuery(feature.get as any, {
        clerk_user_id: body.clerkUserId,
        record_id: body.recordId,
      });
      return json({ ok: true, data: row ?? null });
    }

    // Fallback for domains without a dedicated get function.
    const rows = (await ctx.runQuery(feature.list as any, {
      clerk_user_id: body.clerkUserId,
      limit: 100,
    })) as Array<Record<string, unknown>>;

    const item = rows.find((row) => String(row.id ?? "") === body.recordId) ?? null;
    return json({ ok: true, data: item });
  }),
});

http.route({
  path: "/backend/chat/sessions/create",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, title } = (await req.json()) as { clerkUserId: string; title: string };

    const session = await ctx.runMutation("chat:createSession" as any, {
      clerk_user_id: clerkUserId,
      title: title || "Nutrition Chat",
    });

    return json({ ok: true, data: session });
  }),
});

http.route({
  path: "/backend/chat/sessions/update",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, sessionId, payload } = (await req.json()) as {
      clerkUserId: string;
      sessionId: string;
      payload: Record<string, unknown>;
    };

    const updated = await ctx.runMutation("chat:updateSession" as any, {
      clerk_user_id: clerkUserId,
      session_id: sessionId,
      payload,
    });

    return json({ ok: true, data: updated ?? null });
  }),
});

http.route({
  path: "/backend/chat/sessions/list",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, limit = 30 } = (await req.json()) as { clerkUserId: string; limit?: number };

    const sessions = (await ctx.runQuery("chat:listSessions" as any, {
      clerk_user_id: clerkUserId,
      limit: Math.min(Math.max(limit, 1), 100),
    })) as Array<Record<string, unknown>>;

    return json({ ok: true, data: { items: sessions.map(normalizeChatSession) } });
  }),
});

http.route({
  path: "/backend/chat/messages/add",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, sessionId, role, content, metadata } = (await req.json()) as {
      clerkUserId: string;
      sessionId: string;
      role: string;
      content: string;
      metadata?: Record<string, unknown>;
    };

    try {
      const message = (await ctx.runMutation("chat:addMessage" as any, {
        clerk_user_id: clerkUserId,
        session_id: sessionId,
        role,
        content,
        metadata,
      })) as Record<string, unknown>;

      return json({ ok: true, data: normalizeChatMessage(message) });
    } catch {
      return json({ ok: false, error: "session_not_found" }, 404);
    }
  }),
});

http.route({
  path: "/backend/chat/actions/create",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, sessionId, payload } = (await req.json()) as {
      clerkUserId: string;
      sessionId: string;
      payload: Record<string, unknown>;
    };

    const action = (await ctx.runMutation("chat:createAction" as any, {
      clerk_user_id: clerkUserId,
      session_id: sessionId,
      payload,
    })) as Record<string, unknown>;

    return json({ ok: true, data: normalizeChatAction(action) });
  }),
});

http.route({
  path: "/backend/chat/actions/get",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, sessionId, actionId } = (await req.json()) as {
      clerkUserId: string;
      sessionId: string;
      actionId: string;
    };

    const action = (await ctx.runQuery("chat:getAction" as any, {
      clerk_user_id: clerkUserId,
      session_id: sessionId,
      action_id: actionId,
    })) as Record<string, unknown> | null;

    return json({ ok: true, data: action ? normalizeChatAction(action) : null });
  }),
});

http.route({
  path: "/backend/chat/actions/update",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, sessionId, actionId, payload } = (await req.json()) as {
      clerkUserId: string;
      sessionId: string;
      actionId: string;
      payload: Record<string, unknown>;
    };

    const action = (await ctx.runMutation("chat:updateAction" as any, {
      clerk_user_id: clerkUserId,
      session_id: sessionId,
      action_id: actionId,
      payload,
    })) as Record<string, unknown> | null;

    return json({ ok: true, data: action ? normalizeChatAction(action) : null });
  }),
});

http.route({
  path: "/backend/chat/messages/list",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, sessionId, limit = 100 } = (await req.json()) as {
      clerkUserId: string;
      sessionId: string;
      limit?: number;
    };

    const messages = (await ctx.runQuery("chat:listMessages" as any, {
      clerk_user_id: clerkUserId,
      session_id: sessionId,
      limit: Math.min(Math.max(limit, 1), 500),
    })) as Array<Record<string, unknown>>;

    return json({ ok: true, data: { items: messages.map(normalizeChatMessage) } });
  }),
});

http.route({
  path: "/backend/quizzes/sessions/create",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, payload } = (await req.json()) as {
      clerkUserId: string;
      payload: Record<string, unknown>;
    };

    const session = await ctx.runMutation("quizzes:createSession" as any, {
      clerk_user_id: clerkUserId,
      payload,
    });

    return json({ ok: true, data: session });
  }),
});

http.route({
  path: "/backend/quizzes/sessions/get",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, sessionId } = (await req.json()) as { clerkUserId: string; sessionId: string };

    const session = await ctx.runQuery("quizzes:getSession" as any, {
      clerk_user_id: clerkUserId,
      session_id: sessionId,
    });

    return json({ ok: true, data: session ?? null });
  }),
});

http.route({
  path: "/backend/quizzes/submissions/create",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, sessionId, payload } = (await req.json()) as {
      clerkUserId: string;
      sessionId: string;
      payload: Record<string, unknown>;
    };

    const submission = await ctx.runMutation("quizzes:createSubmission" as any, {
      clerk_user_id: clerkUserId,
      session_id: sessionId,
      payload,
    });

    return json({ ok: true, data: submission });
  }),
});

http.route({
  path: "/backend/quizzes/history/list",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, limit = 20 } = (await req.json()) as { clerkUserId: string; limit?: number };

    const items = await ctx.runQuery("quizzes:listHistory" as any, {
      clerk_user_id: clerkUserId,
      limit: Math.min(Math.max(limit, 1), 100),
    });

    return json({ ok: true, data: { items } });
  }),
});

http.route({
  path: "/backend/articles/list",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { query, limit = 50 } = (await req.json()) as { query?: string | null; limit?: number };

    const queryArgs: { limit: number; query_text?: string } = {
      limit: Math.min(Math.max(limit, 1), 200),
    };
    if (typeof query === "string" && query.trim()) {
      queryArgs.query_text = query.trim();
    }

    const rows = (await ctx.runQuery("articles:list" as any, queryArgs)) as Array<Record<string, unknown>>;

    return json({ ok: true, data: { items: rows.map(normalizeArticle) } });
  }),
});

http.route({
  path: "/backend/articles/get",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { slug } = (await req.json()) as { slug: string };

    const row = (await ctx.runQuery("articles:getBySlug" as any, {
      slug,
    })) as Record<string, unknown> | null;

    return json({ ok: true, data: row ? normalizeArticle(row) : null });
  }),
});

http.route({
  path: "/backend/articles/seed",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { items } = (await req.json()) as { items: Array<Record<string, unknown>> };

    const inserted = await ctx.runMutation("articles:seed" as any, { items });

    return json({ ok: true, data: { inserted } });
  }),
});

http.route({
  path: "/backend/users/upsert",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, payload } = (await req.json()) as {
      clerkUserId: string;
      payload: Record<string, unknown>;
    };

    const user = await ctx.runMutation("users:upsert" as any, {
      clerk_user_id: clerkUserId,
      ...payload,
    });

    return json({ ok: true, data: user });
  }),
});

http.route({
  path: "/backend/subscriptions/get",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId } = (await req.json()) as { clerkUserId: string };
    const row = (await ctx.runQuery("subscriptions:getByUser" as any, {
      clerk_user_id: clerkUserId,
    })) as Record<string, unknown> | null;

    return json({ ok: true, data: row ? normalizeSubscription(row) : null });
  }),
});

http.route({
  path: "/backend/subscriptions/upsert",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, payload } = (await req.json()) as {
      clerkUserId: string;
      payload: Record<string, unknown>;
    };

    const row = (await ctx.runMutation("subscriptions:upsert" as any, {
      clerk_user_id: clerkUserId,
      payload,
    })) as Record<string, unknown>;

    return json({ ok: true, data: normalizeSubscription(row) });
  }),
});

http.route({
  path: "/backend/subscriptions/events/add",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, eventType, payload } = (await req.json()) as {
      clerkUserId: string;
      eventType: string;
      payload: Record<string, unknown>;
    };

    const event = await ctx.runMutation("subscriptions:addEvent" as any, {
      clerk_user_id: clerkUserId,
      event_type: eventType,
      payload,
    });

    return json({ ok: true, data: event });
  }),
});

http.route({
  path: "/backend/subscriptions/events/list",
  method: "POST",
  handler: httpAction(async (ctx, req) => {
    if (!ensureBackendSecret(req)) return json({ ok: false, error: "unauthorized" }, 401);

    const { clerkUserId, limit = 50 } = (await req.json()) as { clerkUserId: string; limit?: number };

    const items = await ctx.runQuery("subscriptions:listEvents" as any, {
      clerk_user_id: clerkUserId,
      limit: Math.min(Math.max(limit, 1), 200),
    });

    return json({ ok: true, data: { items } });
  }),
});

export default http;
