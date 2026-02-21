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
import type { MealPlanGenerateRequest, MealPlanResponse } from "@/types/api";

const defaults: MealPlanGenerateRequest = {
  gender: "Male",
  goal: "Gain Weight",
  diet_choice: "Vegetarian",
  issue: "No issue",
  gym: "do gym/workout",
  height: "",
  weight: "",
  food_type: "Indian type",
};

export default function MealPlannerPage() {
  const api = useApiClient();
  const { user } = useUser();

  const [form, setForm] = useState<MealPlanGenerateRequest>(defaults);
  const [result, setResult] = useState<MealPlanResponse | null>(null);
  const [pdfName, setPdfName] = useState("");
  const [pdfAge, setPdfAge] = useState<number>(28);

  const { data: history, loading: historyLoading, refreshInBackground } = useConvexHistory<MealPlanResponse>({
    functionName: "mealPlans:listByUser",
    clerkUserId: user?.id,
    limit: 20,
    pollIntervalMs: 25000,
  });

  const { execute, loading, error } = useAsyncAction(async () => api.generateMealPlan(form));

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const payload = await execute();
    if (payload) {
      setResult(payload);
      refreshInBackground();
    }
  }

  async function downloadPdf() {
    if (!result) return;
    const blob = await api.exportMealPlanPdf(result.id, pdfName || "User", pdfAge);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `nutriai_meal_plan_${(pdfName || "user").toLowerCase().replace(/\s+/g, "_")}.pdf`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <FeatureShell
      title="Meal Planner"
      description="Generate personalized meal plans and export polished PDFs for follow-through."
      aside={
        <HistoryPanel title="Recent Meal Plans" loading={historyLoading} empty={!history.length} syncing={loading}>
          {history.map((item) => (
            <button
              key={item.id}
              className="w-full rounded-xl border border-surface-200 bg-surface-50 p-3 text-left"
              onClick={() => setResult(item)}
            >
              <p className="text-sm font-semibold text-accent-800">{new Date(item.created_at).toLocaleString()}</p>
              <p className="mt-1 text-xs text-accent-600">{item.sections.length} sections</p>
            </button>
          ))}
        </HistoryPanel>
      }
    >
      <form className="grid gap-3 sm:grid-cols-2" onSubmit={onSubmit}>
        <Select value={form.gender} onChange={(e) => setForm((s) => ({ ...s, gender: e.target.value }))}>
          <option>Male</option>
          <option>Female</option>
        </Select>
        <Select value={form.goal} onChange={(e) => setForm((s) => ({ ...s, goal: e.target.value }))}>
          <option>Gain Weight</option>
          <option>Loss fat</option>
          <option>Maintain weight</option>
          <option>Gain muscle</option>
          <option>Improve overall health</option>
        </Select>
        <Select value={form.diet_choice} onChange={(e) => setForm((s) => ({ ...s, diet_choice: e.target.value }))}>
          <option>Vegetarian</option>
          <option>Vegan</option>
          <option>Non-vegetarian</option>
          <option>Eggeterian</option>
        </Select>
        <Select value={form.issue} onChange={(e) => setForm((s) => ({ ...s, issue: e.target.value }))}>
          <option>No issue</option>
          <option>Lactose intolerant</option>
          <option>Gluten-free</option>
          <option>Nut allergy</option>
          <option>Other</option>
        </Select>
        <Select value={form.gym} onChange={(e) => setForm((s) => ({ ...s, gym: e.target.value }))}>
          <option>do gym/workout</option>
          <option>do not gym/workout</option>
        </Select>
        <Select value={form.food_type} onChange={(e) => setForm((s) => ({ ...s, food_type: e.target.value }))}>
          <option>Indian type</option>
          <option>Continental type</option>
          <option>World wide type</option>
        </Select>
        <Input
          placeholder="Height (e.g., 180cm)"
          value={form.height}
          onChange={(e) => setForm((s) => ({ ...s, height: e.target.value }))}
        />
        <Input
          placeholder="Weight (e.g., 69kg)"
          value={form.weight}
          onChange={(e) => setForm((s) => ({ ...s, weight: e.target.value }))}
        />

        <div className="sm:col-span-2">
          <Button type="submit" disabled={loading}>
            {loading ? "Generating..." : "Generate Meal Plan"}
          </Button>
        </div>
      </form>

      {error ? <Alert variant="error">{error}</Alert> : null}

      {result ? (
        <div className="mt-6 space-y-4">
          <ResultBlock title="Meal Plan Output">
            <div className="space-y-3">
              {result.sections.map((section) => (
                <div key={section.name} className="rounded-xl border border-surface-200 p-3">
                  <p className="text-sm font-semibold text-accent-800">{section.name}</p>
                  <ul className="mt-2 space-y-1 text-sm text-accent-700">
                    {section.options.map((option, index) => (
                      <li key={`${section.name}-${index}`}>{option}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </ResultBlock>

          <ResultBlock title="Export PDF">
            <div className="grid gap-3 sm:grid-cols-[1fr_140px_auto]">
              <Input placeholder="Full name" value={pdfName} onChange={(e) => setPdfName(e.target.value)} />
              <Input
                placeholder="Age"
                type="number"
                value={pdfAge}
                onChange={(e) => setPdfAge(Number(e.target.value || 0))}
              />
              <Button type="button" onClick={downloadPdf}>
                Download PDF
              </Button>
            </div>
          </ResultBlock>
        </div>
      ) : null}
    </FeatureShell>
  );
}
