import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  users: defineTable({
    clerk_user_id: v.string(),
    email: v.optional(v.string()),
    name: v.optional(v.string()),
    image_url: v.optional(v.string()),
    created_at: v.string(),
  }).index("by_clerk_user_id", ["clerk_user_id"]),

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
    created_at: v.string(),
  }).index("by_user_session_created", ["clerk_user_id", "session_id", "created_at"]),

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
});
