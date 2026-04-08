import type {
  Article,
  BMIResponse,
  CaloriesResponse,
  CalculationHistoryItem,
  ChatContextSection,
  ChatMessage,
  ChatPendingAction,
  ChatSession,
  ChatSessionDeleteResult,
  ChatStreamEvent,
  CreateCheckoutSessionResponse,
  CurrencyCode,
  DemoUserRecord,
  FoodInsightResponse,
  IngredientCheckResponse,
  MealPlanGenerateRequest,
  MealPlanPdfExportResponse,
  MealPlanResponse,
  PlanTier,
  PricingCatalogResponse,
  QuizHistoryItem,
  QuizSessionResponse,
  QuizSubmitResponse,
  RecipeResponse,
  RecommendationResponse,
  SubscriptionEvent,
  SubscriptionResponse,
  SubscriptionUsageResponse,
  RecommendationType,
  RecipeType,
  ShoppingLinksResponse,
} from "@/types/api";
import { captureEvent } from "@/lib/posthog";
import {
  buildClientCorrelationHeaders,
  createRequestCorrelation,
  emitFrontendTelemetry,
  type FrontendTelemetryIdentity,
} from "@/lib/telemetry";

interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
}

interface RequestAnalyticsOptions {
  category?: "api" | "llm" | "billing" | "content" | "workflow";
  feature?: string;
  properties?: Record<string, unknown>;
}

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export class APIClient {
  private baseUrl: string;
  private tokenProvider?: () => Promise<string | null>;
  private devUserIdProvider?: () => Promise<string | null>;
  private emailProvider?: () => Promise<string | null>;

  constructor(options?: {
    tokenProvider?: () => Promise<string | null>;
    devUserIdProvider?: () => Promise<string | null>;
    emailProvider?: () => Promise<string | null>;
  }) {
    this.baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8008";
    this.tokenProvider = options?.tokenProvider;
    this.devUserIdProvider = options?.devUserIdProvider;
    this.emailProvider = options?.emailProvider;
  }

  private resolveFallbackBaseUrl(): string | null {
    try {
      const url = new URL(this.baseUrl);
      if (url.hostname === "localhost") {
        url.hostname = "127.0.0.1";
        return url.toString().replace(/\/$/, "");
      }
      if (url.hostname === "127.0.0.1") {
        url.hostname = "localhost";
        return url.toString().replace(/\/$/, "");
      }
      return null;
    } catch {
      return null;
    }
  }

  private async fetchWithFallback(path: string, init: RequestInit): Promise<Response> {
    const primaryUrl = `${this.baseUrl}${path}`;
    try {
      return await fetch(primaryUrl, init);
    } catch {
      const fallbackBaseUrl = this.resolveFallbackBaseUrl();
      if (!fallbackBaseUrl || fallbackBaseUrl === this.baseUrl) {
        throw new ApiError("Cannot connect to backend. Please make sure FastAPI is running on port 8008.", 0, "NETWORK_ERROR");
      }

      try {
        return await fetch(`${fallbackBaseUrl}${path}`, init);
      } catch {
        throw new ApiError(
          "Cannot connect to backend. Please make sure FastAPI is running on port 8008.",
          0,
          "NETWORK_ERROR"
        );
      }
    }
  }

  private async getAuthHeader(): Promise<Record<string, string>> {
    if (!this.tokenProvider) return {};
    const token = await this.tokenProvider();
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
  }

  private async getDevUserHeader(): Promise<Record<string, string>> {
    if (!this.devUserIdProvider) return {};
    const userId = await this.devUserIdProvider();
    if (!userId) return {};
    return { "x-dev-user-id": userId };
  }

  private async getIdentity(): Promise<FrontendTelemetryIdentity> {
    const [clerkUserId, email] = await Promise.all([
      this.devUserIdProvider ? this.devUserIdProvider() : Promise.resolve(null),
      this.emailProvider ? this.emailProvider() : Promise.resolve(null),
    ]);

    return {
      clerk_user_id: clerkUserId ?? undefined,
      email: email ?? undefined,
    };
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    return this.requestWithAnalytics(path, init);
  }

  private deriveAnalytics(path: string, init: RequestInit, analytics?: RequestAnalyticsOptions): RequestAnalyticsOptions {
    if (analytics) {
      return analytics;
    }

    const method = (init.method ?? "GET").toUpperCase();
    const base: RequestAnalyticsOptions = {
      category: "api",
      feature: "general",
      properties: {
        method,
      },
    };

    if (path.includes("/food-insights/")) return { ...base, category: "llm", feature: "food_insight" };
    if (path.includes("/ingredient-checks/")) return { ...base, category: "llm", feature: "ingredient_checker" };
    if (path.includes("/meal-plans/")) return { ...base, category: "llm", feature: "meal_planner" };
    if (path.includes("/recipes/")) return { ...base, category: "llm", feature: "recipe_finder" };
    if (path.includes("/quizzes/")) return { ...base, category: "llm", feature: "nutri_quiz" };
    if (path.includes("/nutri-chat/")) return { ...base, category: "llm", feature: "nutri_chat" };
    if (path.includes("/recommendations/")) return { ...base, category: "llm", feature: "recommendations" };
    if (path.includes("/calculators/")) return { ...base, category: "workflow", feature: "nutri_calc" };
    if (path.includes("/subscriptions/")) return { ...base, category: "billing", feature: "subscription" };
    if (path.includes("/articles")) return { ...base, category: "content", feature: "articles" };

    return base;
  }

  private captureRequestEvent(
    phase: "completed" | "failed",
    path: string,
    method: string,
    latencyMs: number,
    analytics: RequestAnalyticsOptions,
    extra: Record<string, unknown>,
    identity: FrontendTelemetryIdentity
  ): void {
    const properties = {
      category: analytics.category ?? "api",
      feature: analytics.feature ?? "general",
      path,
      method,
      latency_ms: latencyMs,
      ...analytics.properties,
      ...extra,
    };

    captureEvent(`frontend_api_request_${phase}`, properties);
    void emitFrontendTelemetry(
      {
        event_type: `frontend_api_request_${phase}`,
        category: analytics.category ?? "api",
        feature: analytics.feature ?? "general",
        status: phase,
        path,
        request_id: typeof extra.request_id === "string" ? extra.request_id : undefined,
        backend_request_id:
          typeof extra.backend_request_id === "string" ? extra.backend_request_id : undefined,
        properties,
      },
      identity
    );

    if (analytics.category === "llm") {
      captureEvent(`frontend_llm_request_${phase}`, properties);
    }
  }

  private async requestWithAnalytics<T>(
    path: string,
    init: RequestInit = {},
    analytics?: RequestAnalyticsOptions
  ): Promise<T> {
    const correlation = createRequestCorrelation();
    const identity = await this.getIdentity();
    const headers: HeadersInit = {
      ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(await this.getAuthHeader()),
      ...(await this.getDevUserHeader()),
      ...buildClientCorrelationHeaders(correlation, identity),
      ...(init.headers ?? {}),
    };
    const startedAt = performance.now();
    const method = (init.method ?? "GET").toUpperCase();
    const resolvedAnalytics = this.deriveAnalytics(path, init, analytics);

    let response: Response;

    try {
      response = await this.fetchWithFallback(path, {
        ...init,
        headers,
      });
    } catch (error) {
      this.captureRequestEvent(
        "failed",
        path,
        method,
        Math.round(performance.now() - startedAt),
        resolvedAnalytics,
        {
          status_code: 0,
          request_id: correlation.requestId,
          backend_request_id: null,
          error_code: error instanceof ApiError ? error.code ?? "NETWORK_ERROR" : "NETWORK_ERROR",
          error_message: error instanceof Error ? error.message : "Network error",
        },
        identity
      );
      throw error;
    }

    const backendRequestId = response.headers.get("x-request-id");

    if (!response.ok) {
      let payload: ApiErrorPayload = {};
      try {
        payload = await response.json();
      } catch {
        payload = {};
      }
      const message = payload.error?.message ?? `Request failed with status ${response.status}`;
      this.captureRequestEvent(
        "failed",
        path,
        method,
        Math.round(performance.now() - startedAt),
        resolvedAnalytics,
        {
          status_code: response.status,
          request_id: correlation.requestId,
          backend_request_id: backendRequestId,
          error_code: payload.error?.code ?? "REQUEST_FAILED",
          error_message: message,
        },
        identity
      );
      throw new ApiError(message, response.status, payload.error?.code, payload.error?.details);
    }

    this.captureRequestEvent(
      "completed",
      path,
      method,
      Math.round(performance.now() - startedAt),
      resolvedAnalytics,
      {
        status_code: response.status,
        request_id: correlation.requestId,
        backend_request_id: backendRequestId,
      },
      identity
    );

    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  }

  async health(): Promise<{ status: string; service: string; version: string }> {
    return this.request("/api/v1/health");
  }

  async analyzeFoodText(text: string): Promise<FoodInsightResponse> {
    return this.requestWithAnalytics(
      "/api/v1/food-insights/analyze",
      {
        method: "POST",
        body: JSON.stringify({ input_mode: "text", text }),
      },
      {
        category: "llm",
        feature: "food_insight",
        properties: {
          input_mode: "text",
          input_length: text.trim().length,
        },
      }
    );
  }

  async analyzeFoodImage(file: File): Promise<FoodInsightResponse> {
    const data = new FormData();
    data.append("image", file);
    return this.requestWithAnalytics(
      "/api/v1/food-insights/analyze",
      {
        method: "POST",
        body: data,
      },
      {
        category: "llm",
        feature: "food_insight",
        properties: {
          input_mode: "image",
          file_size_bytes: file.size,
          mime_type: file.type,
        },
      }
    );
  }

  async getFoodHistory(limit = 20): Promise<FoodInsightResponse[]> {
    const payload = await this.request<{ items: FoodInsightResponse[] }>(
      `/api/v1/food-insights/history?limit=${limit}`
    );
    return payload.items;
  }

  async analyzeIngredientsText(ingredientsText: string): Promise<IngredientCheckResponse> {
    return this.requestWithAnalytics(
      "/api/v1/ingredient-checks/analyze",
      {
        method: "POST",
        body: JSON.stringify({ input_mode: "text", ingredients_text: ingredientsText }),
      },
      {
        category: "llm",
        feature: "ingredient_checker",
        properties: {
          input_mode: "text",
          input_length: ingredientsText.trim().length,
        },
      }
    );
  }

  async analyzeIngredientsImage(file: File): Promise<IngredientCheckResponse> {
    const data = new FormData();
    data.append("image", file);
    return this.requestWithAnalytics(
      "/api/v1/ingredient-checks/analyze",
      {
        method: "POST",
        body: data,
      },
      {
        category: "llm",
        feature: "ingredient_checker",
        properties: {
          input_mode: "image",
          file_size_bytes: file.size,
          mime_type: file.type,
        },
      }
    );
  }

  async getIngredientHistory(limit = 20): Promise<IngredientCheckResponse[]> {
    const payload = await this.request<{ items: IngredientCheckResponse[] }>(
      `/api/v1/ingredient-checks/history?limit=${limit}`
    );
    return payload.items;
  }

  async generateMealPlan(input: MealPlanGenerateRequest): Promise<MealPlanResponse> {
    return this.requestWithAnalytics(
      "/api/v1/meal-plans/generate",
      {
        method: "POST",
        body: JSON.stringify(input),
      },
      {
        category: "llm",
        feature: "meal_planner",
        properties: {
          goal: input.goal,
          diet_choice: input.diet_choice,
          food_type: input.food_type,
        },
      }
    );
  }

  async getMealPlanHistory(limit = 20): Promise<MealPlanResponse[]> {
    const payload = await this.request<{ items: MealPlanResponse[] }>(
      `/api/v1/meal-plans/history?limit=${limit}`
    );
    return payload.items;
  }

  async exportMealPlanPdf(recordId: string, fullName: string, age: number): Promise<Blob> {
    const startedAt = performance.now();
    const correlation = createRequestCorrelation();
    const identity = await this.getIdentity();
    const response = await this.fetchWithFallback(`/api/v1/meal-plans/${recordId}/export/pdf`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(await this.getAuthHeader()),
        ...(await this.getDevUserHeader()),
        ...buildClientCorrelationHeaders(correlation, identity),
      },
      body: JSON.stringify({ full_name: fullName, age }),
    });

    if (!response.ok) {
      let payload: ApiErrorPayload = {};
      try {
        payload = await response.json();
      } catch {
        payload = {};
      }
      const message = payload.error?.message ?? `Failed to export PDF (${response.status})`;
      this.captureRequestEvent(
        "failed",
        `/api/v1/meal-plans/${recordId}/export/pdf`,
        "POST",
        Math.round(performance.now() - startedAt),
        {
          category: "workflow",
          feature: "meal_planner",
          properties: {
            export_format: "pdf",
          },
        },
        {
          status_code: response.status,
          request_id: correlation.requestId,
          backend_request_id: response.headers.get("x-request-id"),
          error_code: payload.error?.code ?? "REQUEST_FAILED",
          error_message: message,
        },
        identity
      );
      throw new ApiError(message, response.status, payload.error?.code, payload.error?.details);
    }

    this.captureRequestEvent(
      "completed",
      `/api/v1/meal-plans/${recordId}/export/pdf`,
      "POST",
      Math.round(performance.now() - startedAt),
      {
        category: "workflow",
        feature: "meal_planner",
        properties: {
          export_format: "pdf",
        },
      },
      {
        status_code: response.status,
        request_id: correlation.requestId,
        backend_request_id: response.headers.get("x-request-id"),
      },
      identity
    );

    return response.blob();
  }

  async getMealPlanPdfExports(recordId: string, limit = 20): Promise<MealPlanPdfExportResponse[]> {
    const payload = await this.request<{ items: MealPlanPdfExportResponse[] }>(
      `/api/v1/meal-plans/${recordId}/exports?limit=${limit}`
    );
    return payload.items;
  }

  async downloadSavedMealPlanPdf(exportId: string): Promise<Blob> {
    const correlation = createRequestCorrelation();
    const identity = await this.getIdentity();
    const response = await this.fetchWithFallback(`/api/v1/meal-plans/exports/${exportId}/download`, {
      method: "GET",
      headers: {
        ...(await this.getAuthHeader()),
        ...(await this.getDevUserHeader()),
        ...buildClientCorrelationHeaders(correlation, identity),
      },
    });

    if (!response.ok) {
      let payload: ApiErrorPayload = {};
      try {
        payload = await response.json();
      } catch {
        payload = {};
      }
      const message = payload.error?.message ?? `Failed to download saved PDF (${response.status})`;
      throw new ApiError(message, response.status, payload.error?.code, payload.error?.details);
    }

    return response.blob();
  }

  async generateRecipe(dishName: string, recipeType: RecipeType): Promise<RecipeResponse> {
    return this.requestWithAnalytics(
      "/api/v1/recipes/generate",
      {
        method: "POST",
        body: JSON.stringify({ dish_name: dishName, recipe_type: recipeType }),
      },
      {
        category: "llm",
        feature: "recipe_finder",
        properties: {
          recipe_type: recipeType,
          dish_name_length: dishName.trim().length,
        },
      }
    );
  }

  async getRecipeHistory(limit = 20): Promise<RecipeResponse[]> {
    const payload = await this.request<{ items: RecipeResponse[] }>(`/api/v1/recipes/history?limit=${limit}`);
    return payload.items;
  }

  async getShoppingLinks(ingredients: string[]): Promise<ShoppingLinksResponse> {
    return this.requestWithAnalytics(
      "/api/v1/recipes/shopping-links",
      {
        method: "POST",
        body: JSON.stringify({ ingredients }),
      },
      {
        category: "workflow",
        feature: "recipe_finder",
        properties: {
          ingredient_count: ingredients.length,
        },
      }
    );
  }

  async generateQuiz(topic: string, difficulty: "easy" | "medium" | "hard", questionCount = 5) {
    return this.requestWithAnalytics<QuizSessionResponse>(
      "/api/v1/quizzes/generate",
      {
        method: "POST",
        body: JSON.stringify({ topic, difficulty, question_count: questionCount }),
      },
      {
        category: "llm",
        feature: "nutri_quiz",
        properties: {
          topic_length: topic.trim().length,
          difficulty,
          question_count: questionCount,
        },
      }
    );
  }

  async submitQuiz(
    sessionId: string,
    answers: Array<{ question_index: number; selected_option: string }>
  ): Promise<QuizSubmitResponse> {
    return this.request(`/api/v1/quizzes/${sessionId}/submit`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    });
  }

  async getQuizHistory(limit = 20): Promise<QuizHistoryItem[]> {
    const payload = await this.request<{ items: QuizHistoryItem[] }>(`/api/v1/quizzes/history?limit=${limit}`);
    return payload.items;
  }

  async getQuizSession(sessionId: string): Promise<QuizSessionResponse> {
    return this.request(`/api/v1/quizzes/history/${sessionId}`);
  }

  async createChatSession(title?: string): Promise<ChatSession> {
    return this.requestWithAnalytics(
      "/api/v1/nutri-chat/sessions",
      {
        method: "POST",
        body: JSON.stringify({ title }),
      },
      {
        category: "workflow",
        feature: "nutri_chat",
        properties: {
          has_custom_title: Boolean(title?.trim()),
        },
      }
    );
  }

  async listChatSessions(limit = 30): Promise<ChatSession[]> {
    const payload = await this.request<{ items: ChatSession[] }>(`/api/v1/nutri-chat/sessions?limit=${limit}`);
    return payload.items;
  }

  async renameChatSession(sessionId: string, title: string): Promise<ChatSession> {
    return this.requestWithAnalytics(
      `/api/v1/nutri-chat/sessions/${sessionId}`,
      {
        method: "PATCH",
        body: JSON.stringify({ title }),
      },
      {
        category: "workflow",
        feature: "nutri_chat",
        properties: {
          action: "rename_session",
          session_id_present: Boolean(sessionId),
        },
      }
    );
  }

  async deleteChatSession(sessionId: string): Promise<ChatSessionDeleteResult> {
    return this.requestWithAnalytics(
      `/api/v1/nutri-chat/sessions/${sessionId}`,
      {
        method: "DELETE",
      },
      {
        category: "workflow",
        feature: "nutri_chat",
        properties: {
          action: "delete_session",
          session_id_present: Boolean(sessionId),
        },
      }
    );
  }

  async getChatContext(): Promise<ChatContextSection[]> {
    const payload = await this.request<{ items: ChatContextSection[] }>("/api/v1/nutri-chat/context");
    return payload.items;
  }

  async sendChatMessage(sessionId: string, content: string): Promise<ChatMessage> {
    return this.requestWithAnalytics(
      `/api/v1/nutri-chat/sessions/${sessionId}/messages`,
      {
        method: "POST",
        body: JSON.stringify({ content }),
      },
      {
        category: "llm",
        feature: "nutri_chat",
        properties: {
          content_length: content.trim().length,
          has_session_id: Boolean(sessionId),
        },
      }
    );
  }

  async listChatMessages(sessionId: string, limit = 100): Promise<ChatMessage[]> {
    const payload = await this.request<{ session_id: string; messages: ChatMessage[] }>(
      `/api/v1/nutri-chat/sessions/${sessionId}/messages?limit=${limit}`
    );
    return payload.messages;
  }

  async streamChatTurn(
    sessionId: string,
    content: string,
    handlers: {
      onEvent: (event: ChatStreamEvent) => void;
    }
  ): Promise<void> {
    const path = `/api/v1/nutri-chat/sessions/${sessionId}/turns/stream`;
    const startedAt = performance.now();
    const method = "POST";
    const correlation = createRequestCorrelation();
    const identity = await this.getIdentity();
    const analytics = {
      category: "llm" as const,
      feature: "nutri_chat",
      properties: {
        content_length: content.trim().length,
        stream: true,
      },
    };

    const response = await this.fetchWithFallback(path, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(await this.getAuthHeader()),
        ...(await this.getDevUserHeader()),
        ...buildClientCorrelationHeaders(correlation, identity),
      },
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      let payload: ApiErrorPayload = {};
      try {
        payload = await response.json();
      } catch {
        payload = {};
      }
      const message = payload.error?.message ?? `Request failed with status ${response.status}`;
      this.captureRequestEvent(
        "failed",
        path,
        method,
        Math.round(performance.now() - startedAt),
        analytics,
        {
          status_code: response.status,
          request_id: correlation.requestId,
          backend_request_id: response.headers.get("x-request-id"),
          error_code: payload.error?.code ?? "REQUEST_FAILED",
          error_message: message,
        },
        identity
      );
      throw new ApiError(message, response.status, payload.error?.code, payload.error?.details);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      this.captureRequestEvent(
        "failed",
        path,
        method,
        Math.round(performance.now() - startedAt),
        analytics,
        {
          status_code: response.status,
          request_id: correlation.requestId,
          backend_request_id: response.headers.get("x-request-id"),
          error_code: "NO_STREAM",
          error_message: "Streaming response body was not available",
        },
        identity
      );
      throw new ApiError("Streaming response was not available", response.status, "NO_STREAM");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let newlineIndex = buffer.indexOf("\n");
      while (newlineIndex !== -1) {
        const line = buffer.slice(0, newlineIndex).trim();
        buffer = buffer.slice(newlineIndex + 1);
        if (line) {
          handlers.onEvent(JSON.parse(line) as ChatStreamEvent);
        }
        newlineIndex = buffer.indexOf("\n");
      }
    }

    if (buffer.trim()) {
      handlers.onEvent(JSON.parse(buffer.trim()) as ChatStreamEvent);
    }

    this.captureRequestEvent(
      "completed",
      path,
      method,
      Math.round(performance.now() - startedAt),
      analytics,
      {
        status_code: response.status,
        request_id: correlation.requestId,
        backend_request_id: response.headers.get("x-request-id"),
      },
      identity
    );
  }

  async confirmChatAction(sessionId: string, actionId: string): Promise<ChatPendingAction> {
    const payload = await this.request<{ action: ChatPendingAction }>(
      `/api/v1/nutri-chat/sessions/${sessionId}/actions/${actionId}/confirm`,
      {
        method: "POST",
      }
    );
    return payload.action;
  }

  async rejectChatAction(sessionId: string, actionId: string): Promise<ChatPendingAction> {
    const payload = await this.request<{ action: ChatPendingAction }>(
      `/api/v1/nutri-chat/sessions/${sessionId}/actions/${actionId}/reject`,
      {
        method: "POST",
      }
    );
    return payload.action;
  }

  async calculateBMI(weightKg: number, heightCm: number): Promise<BMIResponse> {
    return this.request("/api/v1/calculators/bmi", {
      method: "POST",
      body: JSON.stringify({ weight_kg: weightKg, height_cm: heightCm }),
    });
  }

  async calculateCalories(input: {
    gender: "Male" | "Female";
    weight_kg: number;
    height_cm: number;
    age: number;
    activity_multiplier: number;
  }): Promise<CaloriesResponse> {
    return this.request("/api/v1/calculators/calories", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  async getCalculationHistory(limit = 20): Promise<CalculationHistoryItem[]> {
    const payload = await this.request<{ items: CalculationHistoryItem[] }>(
      `/api/v1/calculators/history?limit=${limit}`
    );
    return payload.items;
  }

  async listArticles(query?: string): Promise<Article[]> {
    const qs = new URLSearchParams();
    if (query) qs.set("query", query);
    const payload = await this.request<{ items: Article[] }>(`/api/v1/articles?${qs.toString()}`);
    return payload.items;
  }

  async getArticle(slug: string): Promise<Article> {
    return this.request(`/api/v1/articles/${slug}`);
  }

  async generateRecommendations(query: string, recommendationType: RecommendationType): Promise<RecommendationResponse> {
    return this.requestWithAnalytics(
      "/api/v1/recommendations/generate",
      {
        method: "POST",
        body: JSON.stringify({ query, recommendation_type: recommendationType }),
      },
      {
        category: "llm",
        feature: "recommendations",
        properties: {
          recommendation_type: recommendationType,
          query_length: query.trim().length,
        },
      }
    );
  }

  async getRecommendationHistory(limit = 20): Promise<RecommendationResponse[]> {
    const payload = await this.request<{ items: RecommendationResponse[] }>(
      `/api/v1/recommendations/history?limit=${limit}`
    );
    return payload.items;
  }

  async getPricingPlans(): Promise<PricingCatalogResponse> {
    return this.request("/api/v1/subscriptions/plans");
  }

  async getCurrentSubscription(): Promise<SubscriptionResponse> {
    return this.request("/api/v1/subscriptions/current");
  }

  async getCurrentSubscriptionUsage(): Promise<SubscriptionUsageResponse> {
    return this.request("/api/v1/subscriptions/usage");
  }

  async getSubscriptionHistory(limit = 50): Promise<SubscriptionEvent[]> {
    const payload = await this.request<{ items: SubscriptionEvent[] }>(`/api/v1/subscriptions/history?limit=${limit}`);
    return payload.items;
  }

  async selectSubscriptionPlan(tier: PlanTier, currency: CurrencyCode): Promise<SubscriptionResponse> {
    return this.requestWithAnalytics(
      "/api/v1/subscriptions/select",
      {
        method: "POST",
        body: JSON.stringify({ tier, currency }),
      },
      {
        category: "billing",
        feature: "subscription",
        properties: {
          tier,
          currency,
        },
      }
    );
  }

  async createCheckoutSession(payload: {
    tier: Extract<PlanTier, "plus" | "pro">;
    currency: CurrencyCode;
    success_url: string;
    cancel_url: string;
  }): Promise<CreateCheckoutSessionResponse> {
    return this.requestWithAnalytics(
      "/api/v1/subscriptions/checkout-session",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      {
        category: "billing",
        feature: "subscription",
        properties: {
          tier: payload.tier,
          currency: payload.currency,
        },
      }
    );
  }

  async confirmCheckoutSession(sessionId: string): Promise<SubscriptionResponse> {
    return this.requestWithAnalytics(
      "/api/v1/subscriptions/checkout/confirm",
      {
        method: "POST",
        body: JSON.stringify({ session_id: sessionId }),
      },
      {
        category: "billing",
        feature: "subscription",
        properties: {
          has_session_id: Boolean(sessionId),
        },
      }
    );
  }

  async seedDemoUsers(): Promise<DemoUserRecord[]> {
    const payload = await this.request<{ users: DemoUserRecord[] }>("/api/v1/subscriptions/demo-users/seed", {
      method: "POST",
    });
    return payload.users;
  }
}
