"use client";

import { useEffect, useMemo, useState } from "react";
import { List, Settings, Search, RefreshCw, FileText, ArrowRight, Sparkles, Check } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FieldLabel } from "@/components/ui/field-label";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useApiClient } from "@/hooks/useApiClient";

type LibraryFeature =
  | "food_insight"
  | "ingredient_check"
  | "meal_plan"
  | "recipe"
  | "quiz"
  | "chat"
  | "calculator"
  | "recommendation";

type LibraryEntry = {
  id: string;
  feature: LibraryFeature;
  featureLabel: string;
  createdAt: string;
  title: string;
  summary: string;
  detail: unknown;
};

type LibrarySettings = {
  units: "metric" | "imperial";
  historyDensity: "compact" | "comfortable";
  defaultFocus: "analyze" | "plan" | "coach" | "track";
  autoHideHistoryPanels: boolean;
  customRule: string;
};

const SETTINGS_STORAGE_KEY = "nutriai_library_settings_v1";

const defaultSettings: LibrarySettings = {
  units: "metric",
  historyDensity: "comfortable",
  defaultFocus: "analyze",
  autoHideHistoryPanels: false,
  customRule: "Keep suggestions practical, budget-aware, and easy to execute on weekdays.",
};

export default function LibraryPage() {
  const api = useApiClient();

  const [activeTab, setActiveTab] = useState<"history" | "settings">("history");
  const [entries, setEntries] = useState<LibraryEntry[]>([]);
  const [selected, setSelected] = useState<LibraryEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | LibraryFeature>("all");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"newest" | "oldest">("newest");
  const [settings, setSettings] = useState<LibrarySettings>(defaultSettings);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(SETTINGS_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<LibrarySettings>;
        setSettings({ ...defaultSettings, ...parsed });
      }
    } catch {
      setSettings(defaultSettings);
    }
  }, []);

  async function loadLibraryData() {
    setLoading(true);
    setError(null);
    try {
      const [food, ingredients, meals, recipes, quizzes, chats, calculations, recommendations] = await Promise.all([
        api.getFoodHistory(30),
        api.getIngredientHistory(30),
        api.getMealPlanHistory(30),
        api.getRecipeHistory(30),
        api.getQuizHistory(30),
        api.listChatSessions(30),
        api.getCalculationHistory(30),
        api.getSmartPicksHistory(30),
      ]);

      const rows: LibraryEntry[] = [
        ...food.map((item) => ({
          id: `food-${item.id}`,
          feature: "food_insight" as const,
          featureLabel: "Food Insight",
          createdAt: item.created_at,
          title: item.verdict,
          summary: `${item.items.length} items analyzed`,
          detail: item,
        })),
        ...ingredients.map((item) => ({
          id: `ingredient-${item.id}`,
          feature: "ingredient_check" as const,
          featureLabel: "Ingredient Checker",
          createdAt: item.created_at,
          title: `${item.healthy_ingredients.length} healthy / ${item.unhealthy_ingredients.length} risky`,
          summary: "Ingredient profile generated",
          detail: item,
        })),
        ...meals.map((item) => ({
          id: `meal-${item.id}`,
          feature: "meal_plan" as const,
          featureLabel: "Meal Planner",
          createdAt: item.created_at,
          title: `${item.sections.length} meal sections`,
          summary: "Meal plan generated",
          detail: item,
        })),
        ...recipes.map((item) => ({
          id: `recipe-${item.id}`,
          feature: "recipe" as const,
          featureLabel: "Recipe Finder",
          createdAt: item.created_at,
          title: item.recipe_name,
          summary: `${item.ingredients.length} ingredients`,
          detail: item,
        })),
        ...quizzes.map((item) => ({
          id: `quiz-${item.session_id}`,
          feature: "quiz" as const,
          featureLabel: "Nutri Quiz",
          createdAt: item.created_at,
          title: item.topic,
          summary: `Score ${item.score_percentage != null ? `${item.score_percentage.toFixed(1)}%` : "pending"}`,
          detail: item,
        })),
        ...chats.map((item) => ({
          id: `chat-${item.session_id}`,
          feature: "chat" as const,
          featureLabel: "Nutri Chat",
          createdAt: item.created_at,
          title: item.title,
          summary: "Session created",
          detail: item,
        })),
        ...calculations.map((item) => ({
          id: `calc-${item.id}`,
          feature: "calculator" as const,
          featureLabel: "Nutri Calc",
          createdAt: item.created_at,
          title: item.calculator_type.toUpperCase(),
          summary: "Calculation record",
          detail: item,
        })),
        ...recommendations.map((item) => ({
          id: `rec-${item.id}`,
          feature: "recommendation" as const,
          featureLabel: "Nutri Smart Picks",
          createdAt: item.created_at,
          title: item.title,
          summary: `${item.ranked_options.length} ranked picks`,
          detail: item,
        })),
      ];

      const sorted = rows.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
      setEntries(sorted);
      setSelected(sorted[0] ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load library history");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadLibraryData();
  }, []);

  async function openEntry(entry: LibraryEntry) {
    if (entry.feature === "chat") {
      const sessionId = entry.id.replace("chat-", "");
      try {
        const messages = await api.listChatMessages(sessionId, 200);
        setSelected({ ...entry, detail: { ...(entry.detail as object), messages } });
        return;
      } catch {
        setSelected(entry);
        return;
      }
    }
    setSelected(entry);
  }

  const visibleEntries = useMemo(() => {
    const text = search.trim().toLowerCase();
    const rows = entries.filter((item) => {
      if (filter !== "all" && item.feature !== filter) return false;
      if (!text) return true;
      return (
        item.featureLabel.toLowerCase().includes(text) ||
        item.title.toLowerCase().includes(text) ||
        item.summary.toLowerCase().includes(text)
      );
    });
    return rows.sort((a, b) =>
      sortBy === "newest"
        ? new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        : new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
    );
  }, [entries, filter, search, sortBy]);

  function saveSettings() {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
    setSaveMsg("Settings saved.");
    setTimeout(() => setSaveMsg(null), 1800);
  }

  return (
    <div className="space-y-8 animate-reveal">
      <section className="flex items-center gap-1 p-1 bg-black/[0.03] rounded-full w-fit">
        <button
          type="button"
          onClick={() => setActiveTab("history")}
          className={`flex items-center gap-2 px-6 py-2.5 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all ${activeTab === "history" ? "bg-white shadow-soft-glow text-vibrant" : "text-foreground/40 hover:text-foreground/60"
            }`}
        >
          <List className="h-3 w-3" />
          History
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("settings")}
          className={`flex items-center gap-2 px-6 py-2.5 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all ${activeTab === "settings" ? "bg-white shadow-soft-glow text-vibrant" : "text-foreground/40 hover:text-foreground/60"
            }`}
        >
          <Settings className="h-3 w-3" />
          Parameters
        </button>
      </section>

      {activeTab === "history" ? (
        <section className="grid gap-8 xl:grid-cols-[400px_minmax(0,1fr)] items-start">
          <div className="space-y-6 rounded-editorial border border-black/[0.03] bg-white/40 p-8 shadow-elegant">
            <div className="space-y-6">
              <div className="relative group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground/20 group-focus-within:text-vibrant transition-colors pointer-events-none" />
                <Input
                  id="library-search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search Archive..."
                  className="pl-12 bg-white/60 border-black/[0.05] focus:border-vibrant rounded-full shadow-sm"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <FieldLabel htmlFor="library-filter" className="text-[10px] font-bold uppercase tracking-widest text-foreground/40 px-2">Sector</FieldLabel>
                  <Select id="library-filter" value={filter} className="bg-white/60 border-black/[0.05] rounded-full text-xs" onChange={(e) => setFilter(e.target.value as "all" | LibraryFeature)}>
                    <option value="all">All</option>
                    <option value="food_insight">Food Insight</option>
                    <option value="ingredient_check">Ingredient</option>
                    <option value="meal_plan">Meal Planner</option>
                    <option value="recipe">Recipe Finder</option>
                    <option value="quiz">Nutri Quiz</option>
                    <option value="chat">Nutri Chat</option>
                    <option value="calculator">Nutri Calc</option>
                    <option value="recommendation">Nutri Smart Picks</option>
                  </Select>
                </div>
                <div className="space-y-2">
                  <FieldLabel htmlFor="library-sort" className="text-[10px] font-bold uppercase tracking-widest text-foreground/40 px-2">Order</FieldLabel>
                  <Select id="library-sort" value={sortBy} className="bg-white/60 border-black/[0.05] rounded-full text-xs" onChange={(e) => setSortBy(e.target.value as "newest" | "oldest")}>
                    <option value="newest">Recent First</option>
                    <option value="oldest">Oldest First</option>
                  </Select>
                </div>
              </div>
              <Button type="button" variant="ghost" className="w-full rounded-full border border-black/[0.03] text-[10px] font-bold uppercase tracking-widest" onClick={() => void loadLibraryData()}>
                <RefreshCw className={`mr-2 h-3 w-3 ${loading ? "animate-spin" : ""}`} />
                Refresh History
              </Button>
            </div>

            {error ? <Alert variant="error" className="rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant">{error}</Alert> : null}

            <div className="max-h-[50vh] space-y-3 overflow-y-auto pr-2 scrollbar-elegant">
              {!loading && !visibleEntries.length ? (
                <div className="py-20 text-center opacity-20 italic">
                  <FileText className="h-12 w-12 mx-auto mb-4" />
                  <p className="text-xs">No history for this filter.</p>
                </div>
              ) : null}
              {visibleEntries.map((entry) => (
                <button
                  key={entry.id}
                  type="button"
                  onClick={() => void openEntry(entry)}
                  className={`w-full rounded-editorial border p-5 text-left transition-all shadow-soft-glow group relative overflow-hidden ${selected?.id === entry.id ? "border-vibrant/40 bg-white/80" : "border-black/[0.03] bg-white/40 hover:border-vibrant/10"
                    }`}
                >
                  {selected?.id === entry.id && (
                    <div className="absolute top-0 left-0 bottom-0 w-1 bg-vibrant" />
                  )}
                  <p className={`text-[9px] font-bold uppercase tracking-widest mb-1 ${selected?.id === entry.id ? "text-vibrant" : "text-foreground/30"}`}>{entry.featureLabel}</p>
                  <p className="text-sm font-semibold text-foreground group-hover:text-vibrant transition-colors truncate">{entry.title}</p>
                  <p className="mt-1 text-[10px] font-medium text-foreground/40 italic leading-snug">{entry.summary}</p>
                  <p className="mt-3 text-[9px] font-bold uppercase tracking-widest text-foreground/20">{new Date(entry.createdAt).toLocaleDateString()}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-editorial border border-black/[0.03] bg-white/60 p-10 shadow-elegant sticky top-12">
            {selected ? (
              <div className="space-y-8 animate-reveal">
                <div className="border-b border-black/[0.03] pb-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Badge className="bg-vibrant/5 text-vibrant border-vibrant/20 rounded-full text-[9px] font-bold uppercase tracking-widest px-4 py-1">{selected.featureLabel}</Badge>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-foreground/20 italic">{new Date(selected.createdAt).toLocaleString()}</p>
                  </div>
                  <h2 className="text-4xl font-display font-semibold text-foreground leading-tight tracking-tight mb-2">{selected.title}</h2>
                  <p className="text-sm font-medium text-foreground/50 italic">{selected.summary}</p>
                </div>

                <div className="space-y-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-foreground/30">Details</p>
                  <pre className="max-h-[50vh] overflow-auto rounded-editorial border border-black/[0.03] bg-black/[0.02] p-8 text-[11px] font-mono leading-relaxed text-foreground/70 custom-scrollbar-minimal">
                    {JSON.stringify(selected.detail, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-20 opacity-20 italic">
                <Search className="h-16 w-16 mb-6 text-foreground" />
                <p className="text-lg">Select any history item to view details.</p>
              </div>
            )}
          </div>
        </section>
      ) : (
        <section className="max-w-4xl mx-auto rounded-editorial border border-black/[0.03] bg-white/60 p-12 shadow-elegant animate-reveal">
          <div className="mb-12 border-b border-black/[0.03] pb-8">
            <h2 className="text-5xl font-display font-semibold text-foreground mb-4">Core Attributes</h2>
            <p className="text-sm font-medium text-foreground/40 italic leading-relaxed">
              Set your preferred units and default page behavior.
            </p>
          </div>

          <div className="grid gap-12 sm:grid-cols-2">
            <div className="space-y-4">
              <FieldLabel htmlFor="settings-units" className="text-[11px] font-bold uppercase tracking-widest text-foreground/40 px-2 italic">Standard Units</FieldLabel>
              <Select
                id="settings-units"
                className="h-14 bg-white/60 border-black/[0.05] rounded-full px-6 shadow-sm"
                value={settings.units}
                onChange={(e) => setSettings((prev) => ({ ...prev, units: e.target.value as "metric" | "imperial" }))}
              >
                <option value="metric">Metric (kg, cm)</option>
                <option value="imperial">Imperial (lb, ft/in)</option>
              </Select>
            </div>
            <div className="space-y-4">
              <FieldLabel htmlFor="settings-density" className="text-[11px] font-bold uppercase tracking-widest text-foreground/40 px-2 italic">Observation Depth</FieldLabel>
              <Select
                id="settings-density"
                className="h-14 bg-white/60 border-black/[0.05] rounded-full px-6 shadow-sm"
                value={settings.historyDensity}
                onChange={(e) => setSettings((prev) => ({ ...prev, historyDensity: e.target.value as "compact" | "comfortable" }))}
              >
                <option value="compact">Condensed View</option>
                <option value="comfortable">Comfortable Exploration</option>
              </Select>
            </div>
            <div className="space-y-4">
              <FieldLabel htmlFor="settings-focus" className="text-[11px] font-bold uppercase tracking-widest text-foreground/40 px-2 italic">Default Intent</FieldLabel>
              <Select
                id="settings-focus"
                className="h-14 bg-white/60 border-black/[0.05] rounded-full px-6 shadow-sm"
                value={settings.defaultFocus}
                onChange={(e) =>
                  setSettings((prev) => ({ ...prev, defaultFocus: e.target.value as "analyze" | "plan" | "coach" | "track" }))
                }
              >
                <option value="analyze">Analyze</option>
                <option value="plan">Plan</option>
                <option value="coach">Coach</option>
                <option value="track">Track</option>
              </Select>
            </div>
            <div className="space-y-4">
              <FieldLabel htmlFor="settings-history-toggle" className="text-[11px] font-bold uppercase tracking-widest text-foreground/40 px-2 italic">Panel Dynamics</FieldLabel>
              <Select
                id="settings-history-toggle"
                className="h-14 bg-white/60 border-black/[0.05] rounded-full px-6 shadow-sm"
                value={settings.autoHideHistoryPanels ? "hidden" : "shown"}
                onChange={(e) => setSettings((prev) => ({ ...prev, autoHideHistoryPanels: e.target.value === "hidden" }))}
              >
                <option value="shown">Unveiled by default</option>
                <option value="hidden">Automated concealment</option>
              </Select>
            </div>
          </div>

          <div className="mt-12 space-y-4">
            <FieldLabel htmlFor="settings-rule" className="text-[11px] font-bold uppercase tracking-widest text-vibrant px-2 italic flex items-center gap-2">
              <Sparkles className="h-3 w-3" />
              Custom Rule
            </FieldLabel>
            <Textarea
              id="settings-rule"
              className="min-h-[160px] bg-white/60 border-black/[0.05] focus:border-vibrant rounded-editorial p-6 shadow-sm font-medium italic text-foreground/80 leading-relaxed"
              value={settings.customRule}
              onChange={(e) => setSettings((prev) => ({ ...prev, customRule: e.target.value }))}
              placeholder="Example: Prefer high-protein meals on weekdays and low-sugar snacks."
            />
          </div>

          <div className="mt-12 flex items-center justify-between p-8 bg-black/[0.01] rounded-editorial border border-black/[0.03]">
            <div className="flex items-center gap-3">
              {saveMsg && (
                <p className="text-xs font-bold uppercase tracking-widest text-success-600 flex items-center gap-2 animate-reveal">
                  <Check className="h-3.5 w-3.5" />
                  {saveMsg}
                </p>
              )}
            </div>
            <Button type="button" size="lg" className="rounded-full bg-vibrant hover:bg-vibrant/90 text-white shadow-soft-glow px-12" onClick={saveSettings}>
              Save Settings
            </Button>
          </div>
        </section>
      )}
    </div>
  );
}
