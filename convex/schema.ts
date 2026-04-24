import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  users: defineTable({
    clerk_user_id: v.string(),
    email: v.optional(v.string()),
    name: v.optional(v.string()),
    image_url: v.optional(v.string()),
    permissions: v.optional(v.any()),
    is_demo: v.optional(v.boolean()),
    tier: v.optional(v.string()),
    created_at: v.string(),
  }).index("by_clerk_user_id", ["clerk_user_id"]),

  subscriptions: defineTable({
    subscription_id: v.string(),
    clerk_user_id: v.string(),
    tier: v.string(),
    status: v.string(),
    currency: v.string(),
    amount: v.number(),
    interval: v.string(),
    permissions: v.any(),
    is_demo: v.optional(v.boolean()),
    stripe_customer_id: v.optional(v.string()),
    stripe_subscription_id: v.optional(v.string()),
    stripe_checkout_session_id: v.optional(v.string()),
    created_at: v.string(),
    updated_at: v.string(),
  })
    .index("by_user", ["clerk_user_id"])
    .index("by_user_updated", ["clerk_user_id", "updated_at"]),

  subscriptionEvents: defineTable({
    event_id: v.string(),
    clerk_user_id: v.string(),
    event_type: v.string(),
    payload: v.any(),
    created_at: v.string(),
  }).index("by_user_created", ["clerk_user_id", "created_at"]),

  subscriptionUsage: defineTable({
    usage_id: v.string(),
    clerk_user_id: v.string(),
    period_key: v.string(),
    period_start: v.string(),
    period_end: v.string(),
    nutrition_credits_used: v.number(),
    chat_messages_used: v.number(),
    pdf_exports_used: v.number(),
    feature_breakdown: v.any(),
    created_at: v.string(),
    updated_at: v.string(),
  })
    .index("by_user_period", ["clerk_user_id", "period_key"])
    .index("by_user_updated", ["clerk_user_id", "updated_at"]),

  foodInsights: defineTable({
    record_id: v.string(),
    clerk_user_id: v.string(),
    operation_id: v.optional(v.string()),
    created_at: v.string(),
    input: v.any(),
    items: v.array(v.any()),
    totals: v.any(),
    verdict: v.string(),
    facts: v.array(v.string()),
    raw_response: v.string(),
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_record", ["clerk_user_id", "record_id"]),

  ingredientChecks: defineTable({
    record_id: v.string(),
    clerk_user_id: v.string(),
    operation_id: v.optional(v.string()),
    created_at: v.string(),
    input: v.any(),
    healthy_ingredients: v.array(v.string()),
    unhealthy_ingredients: v.array(v.string()),
    health_issues: v.any(),
    raw_response: v.string(),
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_record", ["clerk_user_id", "record_id"]),

  mealPlans: defineTable({
    record_id: v.string(),
    clerk_user_id: v.string(),
    operation_id: v.optional(v.string()),
    created_at: v.string(),
    profile: v.any(),
    sections: v.array(v.any()),
    raw_response: v.string(),
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_record", ["clerk_user_id", "record_id"]),

  mealPlanPdfExports: defineTable({
    record_id: v.string(),
    clerk_user_id: v.string(),
    operation_id: v.optional(v.string()),
    meal_plan_record_id: v.string(),
    full_name: v.string(),
    age: v.number(),
    file_name: v.string(),
    mime_type: v.string(),
    byte_size: v.number(),
    pdf_base64: v.string(),
    created_at: v.string(),
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_record", ["clerk_user_id", "record_id"]),

  recipes: defineTable({
    record_id: v.string(),
    clerk_user_id: v.string(),
    operation_id: v.optional(v.string()),
    created_at: v.string(),
    input: v.any(),
    recipe_name: v.string(),
    ingredients: v.array(v.any()),
    steps: v.array(v.string()),
    ingredient_list: v.array(v.string()),
    explanation: v.optional(v.string()),
    raw_response: v.string(),
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_record", ["clerk_user_id", "record_id"]),

  quizSessions: defineTable({
    session_id: v.string(),
    clerk_user_id: v.string(),
    operation_id: v.optional(v.string()),
    topic: v.string(),
    difficulty: v.string(),
    questions: v.array(v.any()),
    raw_response: v.optional(v.string()),
    created_at: v.string(),
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_session", ["clerk_user_id", "session_id"]),

  quizAttempts: defineTable({
    attempt_id: v.string(),
    session_id: v.string(),
    clerk_user_id: v.string(),
    operation_id: v.optional(v.string()),
    total_questions: v.number(),
    correct_answers: v.number(),
    score_percentage: v.number(),
    results: v.array(v.any()),
    created_at: v.string(),
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_session", ["clerk_user_id", "session_id"]),

  chatSessions: defineTable({
    session_id: v.string(),
    clerk_user_id: v.string(),
    title: v.string(),
    created_at: v.string(),
    last_message_at: v.optional(v.string()),
    next_sequence_no: v.optional(v.number()),
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_session", ["clerk_user_id", "session_id"]),

  chatMessages: defineTable({
    message_id: v.string(),
    session_id: v.string(),
    clerk_user_id: v.string(),
    operation_id: v.optional(v.string()),
    sequence_no: v.optional(v.number()),
    role: v.string(),
    content: v.string(),
    metadata: v.optional(v.any()),
    created_at: v.string(),
  }).index("by_user_session_created", ["clerk_user_id", "session_id", "created_at"]),

  chatActions: defineTable({
    action_id: v.string(),
    session_id: v.string(),
    clerk_user_id: v.string(),
    operation_id: v.optional(v.string()),
    kind: v.string(),
    title: v.string(),
    summary: v.string(),
    status: v.string(),
    preview_payload: v.any(),
    created_at: v.string(),
    resolved_at: v.optional(v.string()),
    saved_record_id: v.optional(v.string()),
  })
    .index("by_user_session_action", ["clerk_user_id", "session_id", "action_id"])
    .index("by_user_session_created", ["clerk_user_id", "session_id", "created_at"]),

  calculations: defineTable({
    record_id: v.string(),
    clerk_user_id: v.string(),
    operation_id: v.optional(v.string()),
    idempotency_key: v.optional(v.string()),
    calculator_type: v.string(),
    payload: v.any(),
    result: v.any(),
    created_at: v.string(),
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_record", ["clerk_user_id", "record_id"]),

  articles: defineTable({
    slug: v.string(),
    title: v.string(),
    summary: v.string(),
    content: v.string(),
    created_at: v.string(),
  })
    .index("by_slug", ["slug"])
    .index("by_created", ["created_at"]),

  recommendations: defineTable({
    record_id: v.string(),
    clerk_user_id: v.string(),
    operation_id: v.optional(v.string()),
    title: v.string(),
    decision_summary: v.optional(v.string()),
    best_pick: v.optional(v.string()),
    fallback_rule: v.optional(v.string()),
    ranked_options: v.optional(v.array(v.any())),
    recommendations: v.array(v.string()),
    raw_response: v.string(),
    input: v.any(),
    created_at: v.string(),
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_record", ["clerk_user_id", "record_id"]),

  operations: defineTable({
    operation_id: v.string(),
    clerk_user_id: v.string(),
    feature: v.string(),
    status: v.string(),
    queue_tier: v.string(),
    workload_pool: v.string(),
    resource_scope: v.any(),
    idempotency_key: v.optional(v.string()),
    request_payload: v.any(),
    response_payload: v.optional(v.any()),
    result_ref: v.optional(v.any()),
    sequence_no: v.optional(v.number()),
    request_id: v.optional(v.string()),
    error_code: v.optional(v.string()),
    error_message: v.optional(v.string()),
    enqueued_at: v.string(),
    started_at: v.optional(v.string()),
    finished_at: v.optional(v.string()),
    created_at: v.string(),
    updated_at: v.string(),
  })
    .index("by_user_operation", ["clerk_user_id", "operation_id"])
    .index("by_user_feature_idempotency", ["clerk_user_id", "feature", "idempotency_key"])
    .index("by_user_created", ["clerk_user_id", "created_at"]),
});
