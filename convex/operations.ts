import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

const makeId = () => crypto.randomUUID().replace(/-/g, "");

export const create = mutation({
  args: { clerk_user_id: v.string(), payload: v.any() },
  handler: async (ctx, args) => {
    const now = new Date().toISOString();
    const operation_id = typeof args.payload.operation_id === "string" ? args.payload.operation_id : makeId();
    const doc = {
      operation_id,
      clerk_user_id: args.clerk_user_id,
      feature: String(args.payload.feature ?? ""),
      status: String(args.payload.status ?? "queued"),
      queue_tier: String(args.payload.queue_tier ?? "free"),
      workload_pool: String(args.payload.workload_pool ?? "text_generation"),
      resource_scope: args.payload.resource_scope ?? {},
      idempotency_key: typeof args.payload.idempotency_key === "string" ? args.payload.idempotency_key : undefined,
      request_payload: args.payload.request_payload ?? {},
      response_payload: args.payload.response_payload ?? {},
      result_ref: args.payload.result_ref ?? undefined,
      sequence_no: typeof args.payload.sequence_no === "number" ? args.payload.sequence_no : undefined,
      request_id: typeof args.payload.request_id === "string" ? args.payload.request_id : undefined,
      error_code: typeof args.payload.error_code === "string" ? args.payload.error_code : undefined,
      error_message: typeof args.payload.error_message === "string" ? args.payload.error_message : undefined,
      enqueued_at: typeof args.payload.enqueued_at === "string" ? args.payload.enqueued_at : now,
      started_at: typeof args.payload.started_at === "string" ? args.payload.started_at : undefined,
      finished_at: typeof args.payload.finished_at === "string" ? args.payload.finished_at : undefined,
      created_at: typeof args.payload.created_at === "string" ? args.payload.created_at : now,
      updated_at: typeof args.payload.updated_at === "string" ? args.payload.updated_at : now,
    };
    await ctx.db.insert("operations", doc);
    return doc;
  },
});

export const get = query({
  args: { clerk_user_id: v.string(), operation_id: v.string() },
  handler: async (ctx, args) => {
    const row = await ctx.db
      .query("operations")
      .withIndex("by_user_operation", (q) =>
        q.eq("clerk_user_id", args.clerk_user_id).eq("operation_id", args.operation_id)
      )
      .first();
    if (!row) return null;
    const { _id, _creationTime, ...rest } = row;
    return rest;
  },
});

export const getByIdempotency = query({
  args: { clerk_user_id: v.string(), feature: v.string(), idempotency_key: v.string() },
  handler: async (ctx, args) => {
    const row = await ctx.db
      .query("operations")
      .withIndex("by_user_feature_idempotency", (q) =>
        q.eq("clerk_user_id", args.clerk_user_id).eq("feature", args.feature).eq("idempotency_key", args.idempotency_key)
      )
      .first();
    if (!row) return null;
    const { _id, _creationTime, ...rest } = row;
    return rest;
  },
});

export const update = mutation({
  args: { clerk_user_id: v.string(), operation_id: v.string(), payload: v.any() },
  handler: async (ctx, args) => {
    const row = await ctx.db
      .query("operations")
      .withIndex("by_user_operation", (q) =>
        q.eq("clerk_user_id", args.clerk_user_id).eq("operation_id", args.operation_id)
      )
      .first();
    if (!row) return null;
    const patch = {
      ...args.payload,
      updated_at: new Date().toISOString(),
    };
    await ctx.db.patch(row._id, patch);
    const { _id, _creationTime, ...rest } = { ...row, ...patch };
    return rest;
  },
});
