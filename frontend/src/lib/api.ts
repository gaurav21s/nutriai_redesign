import type {
  Article,
  BMIResponse,
  CaloriesResponse,
  CalculationHistoryItem,
  ChatMessage,
  ChatSession,
  FoodInsightResponse,
  IngredientCheckResponse,
  MealPlanGenerateRequest,
  MealPlanResponse,
  QuizHistoryItem,
  QuizSessionResponse,
  QuizSubmitResponse,
  RecipeResponse,
  RecommendationResponse,
  RecommendationType,
  RecipeType,
  ShoppingLinksResponse,
} from "@/types/api";

interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
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

  constructor(options?: {
    tokenProvider?: () => Promise<string | null>;
    devUserIdProvider?: () => Promise<string | null>;
  }) {
    this.baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8008";
    this.tokenProvider = options?.tokenProvider;
    this.devUserIdProvider = options?.devUserIdProvider;
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

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = {
      ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(await this.getAuthHeader()),
      ...(await this.getDevUserHeader()),
      ...(init.headers ?? {}),
    };

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers,
    });

    if (!response.ok) {
      let payload: ApiErrorPayload = {};
      try {
        payload = await response.json();
      } catch {
        payload = {};
      }
      const message = payload.error?.message ?? `Request failed with status ${response.status}`;
      throw new ApiError(message, response.status, payload.error?.code, payload.error?.details);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  }

  async health(): Promise<{ status: string; service: string; version: string }> {
    return this.request("/api/v1/health");
  }

  async analyzeFoodText(text: string): Promise<FoodInsightResponse> {
    return this.request("/api/v1/food-insights/analyze", {
      method: "POST",
      body: JSON.stringify({ input_mode: "text", text }),
    });
  }

  async analyzeFoodImage(file: File): Promise<FoodInsightResponse> {
    const data = new FormData();
    data.append("image", file);
    return this.request("/api/v1/food-insights/analyze", {
      method: "POST",
      body: data,
    });
  }

  async getFoodHistory(limit = 20): Promise<FoodInsightResponse[]> {
    const payload = await this.request<{ items: FoodInsightResponse[] }>(
      `/api/v1/food-insights/history?limit=${limit}`
    );
    return payload.items;
  }

  async analyzeIngredientsText(ingredientsText: string): Promise<IngredientCheckResponse> {
    return this.request("/api/v1/ingredient-checks/analyze", {
      method: "POST",
      body: JSON.stringify({ input_mode: "text", ingredients_text: ingredientsText }),
    });
  }

  async analyzeIngredientsImage(file: File): Promise<IngredientCheckResponse> {
    const data = new FormData();
    data.append("image", file);
    return this.request("/api/v1/ingredient-checks/analyze", {
      method: "POST",
      body: data,
    });
  }

  async getIngredientHistory(limit = 20): Promise<IngredientCheckResponse[]> {
    const payload = await this.request<{ items: IngredientCheckResponse[] }>(
      `/api/v1/ingredient-checks/history?limit=${limit}`
    );
    return payload.items;
  }

  async generateMealPlan(input: MealPlanGenerateRequest): Promise<MealPlanResponse> {
    return this.request("/api/v1/meal-plans/generate", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  async getMealPlanHistory(limit = 20): Promise<MealPlanResponse[]> {
    const payload = await this.request<{ items: MealPlanResponse[] }>(
      `/api/v1/meal-plans/history?limit=${limit}`
    );
    return payload.items;
  }

  async exportMealPlanPdf(recordId: string, fullName: string, age: number): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/v1/meal-plans/${recordId}/export/pdf`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(await this.getAuthHeader()),
        ...(await this.getDevUserHeader()),
      },
      body: JSON.stringify({ full_name: fullName, age }),
    });

    if (!response.ok) {
      throw new ApiError(`Failed to export PDF (${response.status})`, response.status);
    }

    return response.blob();
  }

  async generateRecipe(dishName: string, recipeType: RecipeType): Promise<RecipeResponse> {
    return this.request("/api/v1/recipes/generate", {
      method: "POST",
      body: JSON.stringify({ dish_name: dishName, recipe_type: recipeType }),
    });
  }

  async getRecipeHistory(limit = 20): Promise<RecipeResponse[]> {
    const payload = await this.request<{ items: RecipeResponse[] }>(`/api/v1/recipes/history?limit=${limit}`);
    return payload.items;
  }

  async getShoppingLinks(ingredients: string[]): Promise<ShoppingLinksResponse> {
    return this.request("/api/v1/recipes/shopping-links", {
      method: "POST",
      body: JSON.stringify({ ingredients }),
    });
  }

  async generateQuiz(topic: string, difficulty: "easy" | "medium" | "hard", questionCount = 5) {
    return this.request<QuizSessionResponse>("/api/v1/quizzes/generate", {
      method: "POST",
      body: JSON.stringify({ topic, difficulty, question_count: questionCount }),
    });
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

  async createChatSession(title?: string): Promise<ChatSession> {
    return this.request("/api/v1/nutri-chat/sessions", {
      method: "POST",
      body: JSON.stringify({ title }),
    });
  }

  async listChatSessions(limit = 30): Promise<ChatSession[]> {
    const payload = await this.request<{ items: ChatSession[] }>(`/api/v1/nutri-chat/sessions?limit=${limit}`);
    return payload.items;
  }

  async sendChatMessage(sessionId: string, content: string): Promise<ChatMessage> {
    return this.request(`/api/v1/nutri-chat/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
  }

  async listChatMessages(sessionId: string, limit = 100): Promise<ChatMessage[]> {
    const payload = await this.request<{ session_id: string; messages: ChatMessage[] }>(
      `/api/v1/nutri-chat/sessions/${sessionId}/messages?limit=${limit}`
    );
    return payload.messages;
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
    return this.request("/api/v1/recommendations/generate", {
      method: "POST",
      body: JSON.stringify({ query, recommendation_type: recommendationType }),
    });
  }

  async getRecommendationHistory(limit = 20): Promise<RecommendationResponse[]> {
    const payload = await this.request<{ items: RecommendationResponse[] }>(
      `/api/v1/recommendations/history?limit=${limit}`
    );
    return payload.items;
  }
}
