"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useUser } from "@clerk/nextjs";
import { Activity, PieChart, Info, ArrowRight, History, Trash2, Check, RefreshCw } from "lucide-react";

import { BMITrendGraph } from "@/components/features/bmi-trend-graph";
import { FeatureShell } from "@/components/features/feature-shell";
import { HistoryPanel } from "@/components/features/history-panel";
import { ResultBlock } from "@/components/features/result-block";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FieldLabel } from "@/components/ui/field-label";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useApiClient } from "@/hooks/useApiClient";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { useConvexHistory } from "@/hooks/useConvexHistory";
import type { BMIResponse, CaloriesResponse, CalculationHistoryItem } from "@/types/api";

type Mode = "bmi" | "calories";
type GraphPoint = { date: string; weightKg: number; heightCm: number; bmi: number };

function getTodayDateKey(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function computeBMI(weightKg: number, heightCm: number): number {
  const meters = heightCm / 100;
  if (meters <= 0) return 0;
  return Number((weightKg / (meters * meters)).toFixed(1));
}

function normalizeGraphPoints(raw: unknown): GraphPoint[] {
  if (!Array.isArray(raw)) return [];
  const rows = raw
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const row = item as Record<string, unknown>;
      const weightKg = Number(row.weightKg ?? 0);
      const heightCm = Number(row.heightCm ?? 0);
      const legacyCreatedAt = String(row.createdAt ?? "");
      const date =
        typeof row.date === "string" && row.date
          ? row.date
          : legacyCreatedAt
            ? legacyCreatedAt.slice(0, 10)
            : getTodayDateKey();
      const bmiRaw = Number(row.bmi ?? 0);
      const bmi = bmiRaw > 0 ? Number(bmiRaw.toFixed(1)) : computeBMI(weightKg, heightCm);

      if (!date || weightKg <= 0 || heightCm <= 0 || bmi <= 0) return null;
      return { date, weightKg, heightCm, bmi };
    })
    .filter((item): item is GraphPoint => Boolean(item));

  const dedupedByDate = new Map<string, GraphPoint>();
  for (const row of rows) {
    dedupedByDate.set(row.date, row);
  }

  return [...dedupedByDate.values()].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
}

function normalizeStoredDates(raw: unknown): string[] {
  if (!Array.isArray(raw)) return [];
  const dates = raw.filter((item): item is string => typeof item === "string" && Boolean(item.trim()));
  return [...new Set(dates)];
}

export default function NutriCalcPage() {
  const api = useApiClient();
  const { user } = useUser();

  const [mode, setMode] = useState<Mode>("bmi");

  const [weightKg, setWeightKg] = useState(70);
  const [heightCm, setHeightCm] = useState(175);

  const [gender, setGender] = useState<"Male" | "Female">("Male");
  const [age, setAge] = useState(28);
  const [activityMultiplier, setActivityMultiplier] = useState(1.55);

  const [bmiResult, setBmiResult] = useState<BMIResponse | null>(null);
  const [caloriesResult, setCaloriesResult] = useState<CaloriesResponse | null>(null);

  const [graphPoints, setGraphPoints] = useState<GraphPoint[]>([]);
  const [storedDates, setStoredDates] = useState<string[]>([]);
  const [graphReady, setGraphReady] = useState(false);
  const [pendingPoint, setPendingPoint] = useState<GraphPoint | null>(null);

  const graphPointsStorageKey = useMemo(
    () => `nutriai_bmi_graph_points_v2_${user?.id ?? "anonymous"}`,
    [user?.id]
  );
  const graphClicksStorageKey = useMemo(
    () => `nutriai_bmi_graph_click_dates_v1_${user?.id ?? "anonymous"}`,
    [user?.id]
  );

  const { data: history, loading: historyLoading, refreshInBackground } = useConvexHistory<CalculationHistoryItem>({
    functionName: "calculations:listByUser",
    clerkUserId: user?.id,
    limit: 20,
    pollIntervalMs: 25000,
  });

  const bmiAction = useAsyncAction(async () => api.calculateBMI(weightKg, heightCm));
  const caloriesAction = useAsyncAction(async () =>
    api.calculateCalories({
      gender,
      weight_kg: weightKg,
      height_cm: heightCm,
      age,
      activity_multiplier: activityMultiplier,
    })
  );

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (mode === "bmi") {
      const result = await bmiAction.execute();
      if (result) {
        setBmiResult(result);
        setPendingPoint({
          date: getTodayDateKey(),
          weightKg,
          heightCm,
          bmi: Number(result.bmi.toFixed(1)),
        });
        refreshInBackground();
      }
      return;
    }

    const result = await caloriesAction.execute();
    if (result) {
      setCaloriesResult(result);
      refreshInBackground();
    }
  }

  const isLoading = bmiAction.loading || caloriesAction.loading;
  const error = bmiAction.error ?? caloriesAction.error;

  useEffect(() => {
    setGraphReady(false);
    try {
      const pointsRaw = localStorage.getItem(graphPointsStorageKey);
      const clicksRaw = localStorage.getItem(graphClicksStorageKey);

      setGraphPoints(normalizeGraphPoints(pointsRaw ? JSON.parse(pointsRaw) : []));
      setStoredDates(normalizeStoredDates(clicksRaw ? JSON.parse(clicksRaw) : []));
    } catch {
      localStorage.removeItem(graphPointsStorageKey);
      localStorage.removeItem(graphClicksStorageKey);
      setGraphPoints([]);
      setStoredDates([]);
    } finally {
      setGraphReady(true);
    }
  }, [graphPointsStorageKey, graphClicksStorageKey]);

  useEffect(() => {
    if (!graphReady) return;
    localStorage.setItem(graphPointsStorageKey, JSON.stringify(graphPoints));
  }, [graphPoints, graphReady, graphPointsStorageKey]);

  useEffect(() => {
    if (!graphReady) return;
    localStorage.setItem(graphClicksStorageKey, JSON.stringify(storedDates));
  }, [storedDates, graphReady, graphClicksStorageKey]);

  const todayDate = getTodayDateKey();
  const storedToday = storedDates.includes(todayDate) || graphPoints.some((item) => item.date === todayDate);

  function storeTodayPoint() {
    if (!pendingPoint || storedToday) return;
    setGraphPoints((prev) =>
      [...prev.filter((item) => item.date !== pendingPoint.date), pendingPoint].sort(
        (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
      )
    );
    setStoredDates((prev) => [...new Set([...prev, pendingPoint.date])]);
    setPendingPoint(null);
  }

  function resetGraph() {
    const confirmReset = window.confirm(
      "Reset metabolic chart? This clears the visual history for the current session."
    );
    if (!confirmReset) return;
    setGraphPoints([]);
    localStorage.setItem(graphPointsStorageKey, JSON.stringify([]));
  }

  return (
    <FeatureShell
      title="Nutri Calc"
      description="Calculate BMI and daily calories. Save one data point per day to your chart."
      aside={
        <HistoryPanel title="Recent Calculations" loading={historyLoading} empty={!history.length} syncing={isLoading}>
          {history.map((item) => (
            <button
              type="button"
              key={item.id}
              className="w-full rounded-editorial border border-black/[0.03] bg-white/40 p-4 text-left shadow-soft-glow transition-all hover:border-vibrant/20 group mb-3 last:mb-0"
              onClick={() => {
                if (item.calculator_type === "bmi") {
                  setMode("bmi");
                  setBmiResult({
                    bmi: Number(item.result.bmi ?? 0),
                    category: String(item.result.category ?? "healthy") as BMIResponse["category"],
                  });
                } else {
                  setMode("calories");
                  setCaloriesResult({
                    bmr: Number(item.result.bmr ?? 0),
                    maintenance_calories: Number(item.result.maintenance_calories ?? 0),
                    guidance: String(item.result.guidance ?? ""),
                  });
                }
              }}
            >
              <div className="flex items-center gap-3 mb-2">
                <RefreshCw className="h-3.5 w-3.5 text-vibrant/40 group-hover:text-vibrant transition-colors" />
                <p className="text-sm font-semibold text-foreground group-hover:text-vibrant transition-colors uppercase tracking-widest text-[10px]">{item.calculator_type}</p>
              </div>
              <p className="text-[9px] font-bold uppercase tracking-widest text-foreground/20 italic">{new Date(item.created_at).toLocaleString()}</p>
            </button>
          ))}
        </HistoryPanel>
      }
    >
      <div className="space-y-8 animate-reveal">
        <div className="flex p-1 bg-black/[0.03] rounded-full w-fit">
          <button
            type="button"
            className={`px-8 py-2.5 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all ${mode === "bmi" ? "bg-white shadow-soft-glow text-vibrant" : "text-foreground/40 hover:text-foreground/60"
              }`}
            onClick={() => setMode("bmi")}
          >
            BMI
          </button>
          <button
            type="button"
            className={`px-8 py-2.5 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all ${mode === "calories" ? "bg-white shadow-soft-glow text-vibrant" : "text-foreground/40 hover:text-foreground/60"
              }`}
            onClick={() => setMode("calories")}
          >
            Calories
          </button>
        </div>

        <form className="grid gap-8 sm:grid-cols-2" onSubmit={onSubmit}>
          <div className="space-y-2">
            <FieldLabel htmlFor="bmi-weight">Weight (kg)</FieldLabel>
            <Input
              id="bmi-weight"
              type="number"
              className="h-14 bg-white/60 border-black/[0.05] focus:border-vibrant rounded-full px-8 shadow-sm"
              value={weightKg}
              onChange={(e) => setWeightKg(Number(e.target.value || 0))}
              placeholder="e.g., 70"
            />
          </div>
          <div className="space-y-2">
            <FieldLabel htmlFor="bmi-height">Height (cm)</FieldLabel>
            <Input
              id="bmi-height"
              type="number"
              className="h-14 bg-white/60 border-black/[0.05] focus:border-vibrant rounded-full px-8 shadow-sm"
              value={heightCm}
              onChange={(e) => setHeightCm(Number(e.target.value || 0))}
              placeholder="e.g., 175"
            />
          </div>

          {mode === "calories" && (
            <>
              <div className="space-y-2">
                <FieldLabel htmlFor="calories-gender">Gender</FieldLabel>
                <Select id="calories-gender" className="h-14 bg-white/60 border-black/[0.05] rounded-full px-6" value={gender} onChange={(e) => setGender(e.target.value as "Male" | "Female")}>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </Select>
              </div>
              <div className="space-y-2">
                <FieldLabel htmlFor="calories-age">Age</FieldLabel>
                <Input
                  id="calories-age"
                  type="number"
                  className="h-14 bg-white/60 border-black/[0.05] rounded-full px-8 shadow-sm"
                  value={age}
                  onChange={(e) => setAge(Number(e.target.value || 0))}
                  placeholder="28"
                />
              </div>
              <div className="sm:col-span-2 space-y-2">
                <FieldLabel htmlFor="calories-activity">Activity Level</FieldLabel>
                <Select
                  id="calories-activity"
                  className="h-14 bg-white/60 border-black/[0.05] rounded-full px-6"
                  value={String(activityMultiplier)}
                  onChange={(e) => setActivityMultiplier(Number(e.target.value))}
                >
                  <option value="1.2">Sedentary [1.2]</option>
                  <option value="1.375">Lightly Active [1.375]</option>
                  <option value="1.55">Moderately Active [1.55]</option>
                  <option value="1.725">Very Active [1.725]</option>
                  <option value="1.9">Very intense [1.9]</option>
                </Select>
              </div>
            </>
          )}

          <div className="sm:col-span-2 pt-4">
            <Button type="submit" size="lg" className="w-full h-14 rounded-full bg-vibrant hover:bg-vibrant/90 text-white shadow-soft-glow transition-all active:scale-95" disabled={isLoading}>
              {isLoading ? "Calculating..." : mode === "bmi" ? "Calculate BMI" : "Calculate Calories"}
            </Button>
          </div>
        </form>

        {error ? <Alert variant="error" className="rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant">{error}</Alert> : null}

        {mode === "bmi" && bmiResult && (
          <div className="grid gap-8 grid-cols-1 md:grid-cols-2">
            <ResultBlock title="BMI Result">
              <div className="flex items-baseline gap-4 mb-4">
                <p className="text-6xl font-display font-semibold text-foreground tracking-tighter">{bmiResult.bmi}</p>
                <p className={`text-[10px] font-bold uppercase tracking-[0.2em] px-4 py-1 rounded-full bg-vibrant/5 text-vibrant border border-vibrant/10`}>
                  {bmiResult.category}
                </p>
              </div>
              <div className="p-4 bg-black/[0.01] rounded-xl border border-black/[0.02]">
                <p className="text-xs font-medium text-foreground/40 italic leading-relaxed">
                  BMI is based on your weight and height.
                </p>
              </div>
            </ResultBlock>

            <ResultBlock title="Save To Daily Graph">
              <div className="space-y-6 self-center">
                <div className="flex flex-wrap items-center gap-4">
                  <Button type="button" size="lg" className="rounded-full bg-foreground text-background px-8 shadow-sm" onClick={storeTodayPoint} disabled={!pendingPoint || storedToday}>
                    {storedToday ? (
                      <div className="flex items-center gap-2">
                        <Check className="h-4 w-4" />
                        Already Saved Today
                      </div>
                    ) : "Save Today's Point"}
                  </Button>
                  {!storedToday && pendingPoint && (
                    <Button type="button" variant="ghost" className="rounded-full text-[10px] font-bold uppercase tracking-widest text-foreground/30 hover:text-foreground/60" onClick={() => setPendingPoint(null)}>
                      Clear
                    </Button>
                  )}
                </div>
                <p className="text-[10px] font-bold uppercase tracking-widest px-1 text-foreground/30 leading-relaxed italic">
                  You can save only one point per day.
                </p>
              </div>
            </ResultBlock>

            <div className="md:col-span-2">
              <BMITrendGraph points={graphPoints} onReset={resetGraph} className="border-none shadow-elegant bg-white/40 p-10 rounded-editorial" />
            </div>
          </div>
        )}

        {mode === "calories" && caloriesResult && (
          <div className="grid gap-8 md:grid-cols-2">
            <ResultBlock title="BMR">
              <div className="flex items-baseline gap-4 mb-2">
                <p className="text-5xl font-display font-semibold text-foreground tracking-tighter">{caloriesResult.bmr.toFixed(0)}</p>
                <span className="text-xs font-bold uppercase tracking-widest text-foreground/30">kcal / day (BMR)</span>
              </div>
              <p className="text-xs font-medium text-foreground/40 italic leading-relaxed">
                Calories your body needs at rest.
              </p>
            </ResultBlock>

            <ResultBlock title="Maintenance Calories" className="bg-vibrant/5 border-vibrant/10">
              <div className="flex items-baseline gap-4 mb-2">
                <p className="text-5xl font-display font-semibold text-vibrant tracking-tighter">{caloriesResult.maintenance_calories.toFixed(0)}</p>
                <span className="text-xs font-bold uppercase tracking-widest text-vibrant/60">kcal / day (Maintenance)</span>
              </div>
              <p className="text-xs font-medium text-vibrant/60 italic leading-relaxed">
                Estimated calories to maintain current weight.
              </p>
            </ResultBlock>

            <ResultBlock title="Guidance" className="md:col-span-2 bg-black/[0.01]">
              <div className="flex gap-6 p-2">
                <div className="mt-1 h-10 w-10 flex items-center justify-center rounded-full bg-vibrant text-white shadow-soft-glow flex-shrink-0">
                  <Info className="h-5 w-5" />
                </div>
                <p className="text-sm font-medium italic text-foreground/70 leading-relaxed">
                  {caloriesResult.guidance}
                </p>
              </div>
            </ResultBlock>
          </div>
        )}
      </div>
    </FeatureShell>
  );
}
