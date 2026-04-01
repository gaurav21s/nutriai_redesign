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

  foodInsights: defineTable({
    record_id: v.string(),
    clerk_user_id: v.string(),
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
    created_at: v.string(),
    profile: v.any(),
    sections: v.array(v.any()),
    raw_response: v.string(),
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_record", ["clerk_user_id", "record_id"]),

  recipes: defineTable({
    record_id: v.string(),
    clerk_user_id: v.string(),
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
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_session", ["clerk_user_id", "session_id"]),

  chatMessages: defineTable({
    message_id: v.string(),
    session_id: v.string(),
    clerk_user_id: v.string(),
    role: v.string(),
    content: v.string(),
    metadata: v.optional(v.any()),
    created_at: v.string(),
  }).index("by_user_session_created", ["clerk_user_id", "session_id", "created_at"]),

  chatActions: defineTable({
    action_id: v.string(),
    session_id: v.string(),
    clerk_user_id: v.string(),
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
    title: v.string(),
    recommendations: v.array(v.string()),
    raw_response: v.string(),
    input: v.any(),
    created_at: v.string(),
  })
    .index("by_user_created", ["clerk_user_id", "created_at"])
    .index("by_user_record", ["clerk_user_id", "record_id"]),
});
