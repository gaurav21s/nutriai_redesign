"use client";

import { FormEvent, useState } from "react";
import { useUser } from "@clerk/nextjs";

import { FeatureShell } from "@/components/features/feature-shell";
import { HistoryPanel } from "@/components/features/history-panel";
import { ResultBlock } from "@/components/features/result-block";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useApiClient } from "@/hooks/useApiClient";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { useConvexHistory } from "@/hooks/useConvexHistory";
import type { BMIResponse, CaloriesResponse, CalculationHistoryItem } from "@/types/api";

type Mode = "bmi" | "calories";

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

  return (
    <FeatureShell
      title="Nutri Calc"
      description="Compute BMI and maintenance calories with persisted calculation history."
      aside={
        <HistoryPanel title="Recent Calculations" loading={historyLoading} empty={!history.length} syncing={isLoading}>
          {history.map((item) => (
            <div key={item.id} className="rounded-xl border border-surface-200 bg-surface-50 p-3">
              <p className="text-sm font-semibold text-accent-800">{item.calculator_type.toUpperCase()}</p>
              <p className="mt-1 text-xs text-accent-600">{new Date(item.created_at).toLocaleString()}</p>
            </div>
          ))}
        </HistoryPanel>
      }
    >
      <div className="space-y-4">
        <div className="flex gap-2">
          <Button type="button" variant={mode === "bmi" ? "primary" : "ghost"} onClick={() => setMode("bmi")}>
            BMI
          </Button>
          <Button type="button" variant={mode === "calories" ? "primary" : "ghost"} onClick={() => setMode("calories")}>
            Calories
          </Button>
        </div>

        <form className="grid gap-3 sm:grid-cols-2" onSubmit={onSubmit}>
          <Input type="number" value={weightKg} onChange={(e) => setWeightKg(Number(e.target.value || 0))} placeholder="Weight (kg)" />
          <Input type="number" value={heightCm} onChange={(e) => setHeightCm(Number(e.target.value || 0))} placeholder="Height (cm)" />

          {mode === "calories" ? (
            <>
              <Select value={gender} onChange={(e) => setGender(e.target.value as "Male" | "Female")}>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </Select>
              <Input type="number" value={age} onChange={(e) => setAge(Number(e.target.value || 0))} placeholder="Age" />
              <Select
                value={String(activityMultiplier)}
                onChange={(e) => setActivityMultiplier(Number(e.target.value))}
                className="sm:col-span-2"
              >
                <option value="1.2">Sedentary (1.2)</option>
                <option value="1.375">Lightly active (1.375)</option>
                <option value="1.55">Moderately active (1.55)</option>
                <option value="1.725">Very active (1.725)</option>
                <option value="1.9">Extra active (1.9)</option>
              </Select>
            </>
          ) : null}

          <div className="sm:col-span-2">
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Calculating..." : mode === "bmi" ? "Calculate BMI" : "Calculate Calories"}
            </Button>
          </div>
        </form>

        {error ? <Alert variant="error">{error}</Alert> : null}

        {bmiResult && mode === "bmi" ? (
          <ResultBlock title="BMI Result">
            <p className="text-2xl font-semibold text-accent-900">{bmiResult.bmi}</p>
            <p className="text-sm uppercase tracking-wide text-accent-600">{bmiResult.category}</p>
          </ResultBlock>
        ) : null}

        {caloriesResult && mode === "calories" ? (
          <ResultBlock title="Calorie Result">
            <p className="text-sm text-accent-700">BMR: {caloriesResult.bmr.toFixed(2)}</p>
            <p className="text-lg font-semibold text-accent-900">
              Maintenance Calories: {caloriesResult.maintenance_calories.toFixed(2)} kcal/day
            </p>
            <p className="text-sm text-accent-600">{caloriesResult.guidance}</p>
          </ResultBlock>
        ) : null}
      </div>
    </FeatureShell>
  );
}
