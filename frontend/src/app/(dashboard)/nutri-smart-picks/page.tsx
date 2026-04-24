"use client";

import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { Apple, ArrowRight, CheckCircle2, Scale, Sparkles } from "lucide-react";

import { FeatureShell } from "@/components/features/feature-shell";
import { HistoryPanel } from "@/components/features/history-panel";
import { ResultBlock } from "@/components/features/result-block";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FieldLabel } from "@/components/ui/field-label";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useApiClient } from "@/hooks/useApiClient";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { useConvexHistory } from "@/hooks/useConvexHistory";
import type { SmartPickGoal, SmartPickMode, SmartPickResponse } from "@/types/api";

const goalOptions: Array<{ value: SmartPickGoal; label: string }> = [
  { value: "fat_loss", label: "Fat loss" },
  { value: "muscle_gain", label: "Muscle gain" },
  { value: "maintenance", label: "Maintenance" },
  { value: "energy_focus", label: "Energy focus" },
  { value: "recovery", label: "Recovery" },
  { value: "healthy_lifestyle", label: "Healthy lifestyle" },
];

const modeOptions: Array<{ value: SmartPickMode; label: string }> = [
  { value: "compare_options", label: "Compare options" },
  { value: "situation_pick", label: "Situation pick" },
  { value: "swap_current_choice", label: "Swap current choice" },
];

function parseMultilineList(value: string): string[] {
  return value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function NutriSmartPicksPageContent() {
  const api = useApiClient();
  const { user } = useUser();
  const searchParams = useSearchParams();

  const [goal, setGoal] = useState<SmartPickGoal>("healthy_lifestyle");
  const [mode, setMode] = useState<SmartPickMode>("situation_pick");
  const [situation, setSituation] = useState("");
  const [optionsText, setOptionsText] = useState("");
  const [currentChoice, setCurrentChoice] = useState("");
  const [constraintsText, setConstraintsText] = useState("");
  const [dietPreference, setDietPreference] = useState("");
  const [budget, setBudget] = useState("");
  const [timeAvailable, setTimeAvailable] = useState("");
  const [cookingAccess, setCookingAccess] = useState("");
  const [context, setContext] = useState("");
  const [result, setResult] = useState<SmartPickResponse | null>(null);

  useEffect(() => {
    const queryGoal = searchParams.get("goal");
    const queryMode = searchParams.get("mode");
    const querySituation = searchParams.get("situation");
    const queryContext = searchParams.get("context");
    const queryCurrentChoice = searchParams.get("current_choice");
    const queryOptions = searchParams.get("options");

    if (queryGoal && goalOptions.some((item) => item.value === queryGoal)) setGoal(queryGoal as SmartPickGoal);
    if (queryMode && modeOptions.some((item) => item.value === queryMode)) setMode(queryMode as SmartPickMode);
    if (querySituation) setSituation(querySituation);
    if (queryContext) setContext(queryContext);
    if (queryCurrentChoice) setCurrentChoice(queryCurrentChoice);
    if (queryOptions) setOptionsText(queryOptions.split("|").join("\n"));
  }, [searchParams]);

  const { data: history, loading: historyLoading, refreshInBackground } = useConvexHistory<SmartPickResponse>({
    functionName: "smartPicks:listByUser",
    clerkUserId: user?.id,
    limit: 20,
    pollIntervalMs: 25000,
  });

  const parsedOptions = useMemo(() => parseMultilineList(optionsText), [optionsText]);
  const parsedConstraints = useMemo(() => parseMultilineList(constraintsText), [constraintsText]);

  const { execute, loading, error } = useAsyncAction(async () =>
    api.generateSmartPicks({
      goal,
      mode,
      situation: situation.trim() || undefined,
      options: parsedOptions.length ? parsedOptions : undefined,
      current_choice: currentChoice.trim() || undefined,
      constraints: parsedConstraints.length ? parsedConstraints : undefined,
      diet_preference: dietPreference.trim() || undefined,
      budget: budget.trim() || undefined,
      time_available: timeAvailable.trim() || undefined,
      cooking_access: cookingAccess.trim() || undefined,
      context: context.trim() || undefined,
    })
  );

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const payload = await execute();
    if (!payload) return;
    setResult(payload);
    refreshInBackground();
  }

  const helperCopy =
    mode === "compare_options"
      ? "Add 2 or more options, one per line. Great for restaurant orders, grocery snacks, or quick meal choices."
      : mode === "swap_current_choice"
        ? "Describe your usual choice or habit, then Nutri Smart Picks will suggest the closest better replacements."
        : "Describe the moment you are in, like office lunch, late-night snack, travel day, or post-workout.";

  return (
    <FeatureShell
      title="Nutri Smart Picks"
      description="Choose the best food option for your goal, situation, and lifestyle."
      aside={
        <HistoryPanel title="Recent Picks" loading={historyLoading} empty={!history.length} syncing={loading}>
          {history.map((item) => (
            <button
              key={item.id}
              className="w-full rounded-editorial border border-black/[0.03] bg-white/40 p-4 text-left transition-all hover:border-vibrant/20 shadow-soft-glow group"
              onClick={() => setResult(item)}
            >
              <div className="mb-2 flex items-center gap-3">
                <Apple className="h-3.5 w-3.5 text-vibrant/40 group-hover:text-vibrant transition-colors" />
                <p className="truncate text-sm font-semibold text-foreground group-hover:text-vibrant transition-colors">
                  {item.title}
                </p>
              </div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-foreground/30">
                Best pick: {item.best_pick}
              </p>
            </button>
          ))}
        </HistoryPanel>
      }
    >
      <form className="space-y-8" onSubmit={onSubmit}>
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
          <div className="space-y-2">
            <FieldLabel htmlFor="smart-picks-goal">Goal</FieldLabel>
            <Select id="smart-picks-goal" value={goal} onChange={(e) => setGoal(e.target.value as SmartPickGoal)}>
              {goalOptions.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-2">
            <FieldLabel htmlFor="smart-picks-mode">Mode</FieldLabel>
            <Select id="smart-picks-mode" value={mode} onChange={(e) => setMode(e.target.value as SmartPickMode)}>
              {modeOptions.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-2">
            <FieldLabel htmlFor="smart-picks-budget">Budget</FieldLabel>
            <Input
              id="smart-picks-budget"
              placeholder="e.g., budget-friendly"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <FieldLabel htmlFor="smart-picks-time">Time Available</FieldLabel>
            <Input
              id="smart-picks-time"
              placeholder="e.g., 10 minutes"
              value={timeAvailable}
              onChange={(e) => setTimeAvailable(e.target.value)}
            />
          </div>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          <div className="space-y-2">
            <FieldLabel htmlFor="smart-picks-diet">Diet Preference</FieldLabel>
            <Input
              id="smart-picks-diet"
              placeholder="e.g., vegetarian"
              value={dietPreference}
              onChange={(e) => setDietPreference(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <FieldLabel htmlFor="smart-picks-cooking-access">Cooking Access</FieldLabel>
            <Input
              id="smart-picks-cooking-access"
              placeholder="e.g., no kitchen, microwave only"
              value={cookingAccess}
              onChange={(e) => setCookingAccess(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <FieldLabel htmlFor="smart-picks-situation">Situation</FieldLabel>
            <Input
              id="smart-picks-situation"
              placeholder="e.g., office lunch, post-workout, travel day"
              value={situation}
              onChange={(e) => setSituation(e.target.value)}
            />
          </div>
        </div>

        {mode === "compare_options" ? (
          <div className="space-y-2">
            <FieldLabel htmlFor="smart-picks-options">Options To Compare</FieldLabel>
            <Textarea
              id="smart-picks-options"
              className="min-h-[140px]"
              placeholder={"Chicken roll\nPaneer wrap\nSalad bowl\nBurger"}
              value={optionsText}
              onChange={(e) => setOptionsText(e.target.value)}
            />
          </div>
        ) : null}

        {mode === "swap_current_choice" ? (
          <div className="space-y-2">
            <FieldLabel htmlFor="smart-picks-current-choice">Current Choice</FieldLabel>
            <Textarea
              id="smart-picks-current-choice"
              className="min-h-[120px]"
              placeholder="e.g., chips and cola at 5 pm, late-night instant noodles, creamy coffee drink"
              value={currentChoice}
              onChange={(e) => setCurrentChoice(e.target.value)}
            />
          </div>
        ) : null}

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <div className="space-y-2">
            <FieldLabel htmlFor="smart-picks-constraints">Constraints</FieldLabel>
            <Textarea
              id="smart-picks-constraints"
              className="min-h-[120px]"
              placeholder={"High protein\nNo sweet drinks\nEating out\nNeed something filling"}
              value={constraintsText}
              onChange={(e) => setConstraintsText(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <FieldLabel htmlFor="smart-picks-context">Extra Context</FieldLabel>
            <Textarea
              id="smart-picks-context"
              className="min-h-[120px]"
              placeholder="Add any extra context about cravings, schedule, training, appetite, or why this decision matters."
              value={context}
              onChange={(e) => setContext(e.target.value)}
            />
          </div>
        </div>

        <div className="rounded-editorial border border-black/[0.04] bg-black/[0.02] px-5 py-4 text-sm text-foreground/55">
          {helperCopy}
        </div>

        <Button
          type="submit"
          size="lg"
          className="rounded-full bg-vibrant px-12 text-white shadow-soft-glow hover:bg-vibrant/90"
          disabled={loading}
        >
          {loading ? "Ranking options..." : "Get Nutri Smart Picks"}
        </Button>
      </form>

      {error ? <Alert variant="error" className="mt-8 rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant">{error}</Alert> : null}

      {result ? (
        <div className="mt-12 space-y-8 animate-reveal">
          <ResultBlock title={result.title}>
            <div className="flex flex-wrap items-center gap-3">
              <Badge className="rounded-full border-none bg-vibrant px-5 py-2 text-[10px] font-bold uppercase tracking-widest text-white">
                Best pick
              </Badge>
              <p className="text-lg font-semibold text-foreground">{result.best_pick}</p>
            </div>
            <p className="mt-5 text-sm leading-7 text-foreground/75">{result.decision_summary}</p>
          </ResultBlock>

          <ResultBlock title="Ranked Options" className="mt-0">
            <div className="grid gap-5 xl:grid-cols-2">
              {result.ranked_options.map((option) => (
                <article
                  key={`${option.rank}-${option.label}`}
                  className="rounded-editorial border border-black/[0.04] bg-white/50 p-6 shadow-soft-glow transition-all hover:border-vibrant/20"
                >
                  <div className="mb-4 flex items-start justify-between gap-4">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-vibrant">Rank {option.rank}</p>
                      <h3 className="mt-2 text-xl font-semibold text-foreground">{option.label}</h3>
                    </div>
                    <div className="rounded-full bg-vibrant/10 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-vibrant">
                      {option.verdict}
                    </div>
                  </div>

                  <div className="space-y-4 text-sm text-foreground/72">
                    <div>
                      <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-foreground/35">Why It Works</p>
                      <p className="leading-7">{option.why}</p>
                    </div>
                    <div>
                      <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-foreground/35">Tradeoff</p>
                      <p className="leading-7">{option.tradeoff}</p>
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="rounded-editorial border border-black/[0.03] bg-black/[0.02] p-4">
                        <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-foreground/35">Quick Upgrade</p>
                        <p className="leading-6">{option.quick_upgrade}</p>
                      </div>
                      <div className="rounded-editorial border border-black/[0.03] bg-black/[0.02] p-4">
                        <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-foreground/35">Good For</p>
                        <p className="leading-6">{option.good_for}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 rounded-editorial border border-vibrant/10 bg-vibrant/5 p-4">
                      <Scale className="mt-0.5 h-4 w-4 flex-shrink-0 text-vibrant" />
                      <div>
                        <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-vibrant">Avoid If</p>
                        <p className="leading-6">{option.avoid_if}</p>
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </ResultBlock>

          <div className="grid gap-6 xl:grid-cols-2">
            <ResultBlock title="Fallback Rule" className="mt-0">
              <div className="flex items-start gap-3 text-sm text-foreground/75">
                <CheckCircle2 className="mt-1 h-4 w-4 flex-shrink-0 text-vibrant" />
                <p className="leading-7">{result.fallback_rule}</p>
              </div>
            </ResultBlock>

            <ResultBlock title="How To Use This" className="mt-0">
              <div className="space-y-3 text-sm text-foreground/75">
                <p className="flex items-start gap-3 leading-7">
                  <Sparkles className="mt-1 h-4 w-4 flex-shrink-0 text-vibrant" />
                  Use the top-ranked option as your default choice whenever this same situation comes up again.
                </p>
                <p className="flex items-start gap-3 leading-7">
                  <ArrowRight className="mt-1 h-4 w-4 flex-shrink-0 text-vibrant" />
                  If you need a cookable dish instead of a situational pick, switch to Recipe Finder from the sidebar.
                </p>
              </div>
            </ResultBlock>
          </div>
        </div>
      ) : null}
    </FeatureShell>
  );
}

export default function NutriSmartPicksPage() {
  return (
    <Suspense fallback={null}>
      <NutriSmartPicksPageContent />
    </Suspense>
  );
}
