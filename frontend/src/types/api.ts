export type InputMode = "text" | "image";

export interface FoodInsightItem {
  name: string;
  quantity: string | null;
  calories_range: string | null;
  carbs_range: string | null;
  fiber_range: string | null;
  protein_range: string | null;
  fats_range: string | null;
  details: string | null;
}

export interface FoodInsightTotals {
  calories: string | null;
  carbs: string | null;
  fiber: string | null;
  protein: string | null;
  fats: string | null;
}

export interface FoodInsightResponse {
  id: string;
  created_at: string;
  items: FoodInsightItem[];
  totals: FoodInsightTotals;
  verdict: string;
  facts: string[];
  raw_response: string;
}

export interface IngredientCheckResponse {
  id: string;
  created_at: string;
  healthy_ingredients: string[];
  unhealthy_ingredients: string[];
  health_issues: Record<string, string[]>;
  raw_response: string;
}

export interface MealPlanSection {
  name: string;
  options: string[];
}

export interface MealPlanGenerateRequest {
  gender: string;
  goal: string;
  diet_choice: string;
  issue: string;
  gym: string;
  height: string;
  weight: string;
  food_type: string;
}

export interface MealPlanResponse {
  id: string;
  created_at: string;
  sections: MealPlanSection[];
  raw_response: string;
}

export type RecipeType = "normal" | "healthier" | "new_healthy";

export interface RecipeIngredient {
  raw: string;
}

export interface ShoppingLinkPair {
  amazon: string;
  blinkit: string;
}

export interface RecipeResponse {
  id: string;
  created_at: string;
  recipe_name: string;
  ingredients: RecipeIngredient[];
  steps: string[];
  ingredient_list: string[];
  shopping_links: Record<string, ShoppingLinkPair>;
  explanation?: string | null;
  raw_response: string;
}

export interface ShoppingLinksResponse {
  links: Record<string, ShoppingLinkPair>;
}

export type QuizDifficulty = "easy" | "medium" | "hard";

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
}

export interface QuizSessionResponse {
  session_id: string;
  topic: string;
  difficulty: QuizDifficulty;
  created_at: string;
  questions: QuizQuestion[];
}

export interface QuizSubmitResponse {
  session_id: string;
  total_questions: number;
  correct_answers: number;
  score_percentage: number;
  results: Array<{
    question_index: number;
    is_correct: boolean;
    selected_option: string;
    correct_option: string;
    explanation: string;
  }>;
}

export interface QuizHistoryItem {
  session_id: string;
  topic: string;
  difficulty: QuizDifficulty;
  created_at: string;
  score_percentage?: number | null;
}

export interface ChatSession {
  session_id: string;
  title: string;
  created_at: string;
  last_message_at?: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface BMIResponse {
  bmi: number;
  category: "underweight" | "healthy" | "overweight" | "obese";
}

export interface CaloriesResponse {
  bmr: number;
  maintenance_calories: number;
  guidance: string;
}

export interface CalculationHistoryItem {
  id: string;
  created_at: string;
  calculator_type: "bmi" | "calories";
  payload: Record<string, unknown>;
  result: Record<string, unknown>;
}

export interface Article {
  id: string;
  slug: string;
  title: string;
  summary: string;
  content: string;
  created_at: string;
}

export type RecommendationType = "healthier_alternative" | "new_healthy_recipe" | "both";

export interface RecommendationResponse {
  id: string;
  created_at: string;
  title: string;
  recommendations: string[];
  raw_response: string;
}

export type CurrencyCode = "USD" | "INR";
export type PlanTier = "free" | "plus" | "pro";
export type SubscriptionStatus = "active" | "trialing" | "canceled" | "incomplete" | "unpaid";

export interface PlanPrice {
  currency: CurrencyCode;
  amount: number;
  interval: "month";
}

export interface PlanSummary {
  tier: PlanTier;
  label: string;
  description: string;
  recommended: boolean;
  features: string[];
  price_usd: PlanPrice;
  price_inr: PlanPrice;
}

export interface PricingCatalogResponse {
  plans: PlanSummary[];
  stripe_publishable_key?: string | null;
}

export interface SubscriptionRecord {
  clerk_user_id: string;
  tier: PlanTier;
  status: SubscriptionStatus;
  currency: CurrencyCode;
  amount: number;
  interval: "month";
  permissions: Record<string, boolean>;
  is_demo: boolean;
  stripe_customer_id?: string | null;
  stripe_subscription_id?: string | null;
  stripe_checkout_session_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionResponse {
  subscription: SubscriptionRecord;
}

export interface SubscriptionEvent {
  id: string;
  clerk_user_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface CreateCheckoutSessionResponse {
  session_id: string;
  checkout_url: string;
}

export interface DemoUserRecord {
  clerk_user_id: string;
  email: string;
  name: string;
  permissions: Record<string, boolean>;
  tier: PlanTier;
  created_at: string;
}
