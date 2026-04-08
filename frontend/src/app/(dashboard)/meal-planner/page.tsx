"use client";

import { FormEvent, useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";

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
import type { MealPlanGenerateRequest, MealPlanPdfExportResponse, MealPlanResponse } from "@/types/api";

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
  const [savedExports, setSavedExports] = useState<MealPlanPdfExportResponse[]>([]);
  const [loadingExports, setLoadingExports] = useState(false);

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
    const exports = await api.getMealPlanPdfExports(result.id, 20);
    setSavedExports(exports);
  }

  async function downloadSavedPdf(item: MealPlanPdfExportResponse) {
    const blob = await api.downloadSavedMealPlanPdf(item.id);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = item.file_name;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  useEffect(() => {
    async function loadSavedExports() {
      if (!result?.id) {
        setSavedExports([]);
        return;
      }
      setLoadingExports(true);
      try {
        const exports = await api.getMealPlanPdfExports(result.id, 20);
        setSavedExports(exports);
      } finally {
        setLoadingExports(false);
      }
    }

    void loadSavedExports();
  }, [api, result?.id]);

  return (
    <FeatureShell
      title="Meal Planner"
      description="Generate personalized meal plans and export polished PDFs for follow-through."
      aside={
        <HistoryPanel title="Recent Meal Plans" loading={historyLoading} empty={!history.length} syncing={loading}>
          {history.map((item) => (
            <button
              key={item.id}
              className="w-full rounded-editorial border border-black/[0.03] bg-white/40 backdrop-blur-sm p-4 text-left transition-all hover:border-vibrant/20 shadow-soft-glow group"
              onClick={() => setResult(item)}
            >
              <p className="text-sm font-semibold text-foreground group-hover:text-vibrant transition-colors">{new Date(item.created_at).toLocaleString()}</p>
              <p className="mt-1 text-[10px] font-bold uppercase tracking-widest text-foreground/30">{item.sections.length} sections</p>
            </button>
          ))}
        </HistoryPanel>
      }
    >
      <form className="grid gap-6 sm:grid-cols-2" onSubmit={onSubmit}>
        <div className="space-y-2">
          <FieldLabel htmlFor="meal-gender">Gender</FieldLabel>
          <Select id="meal-gender" value={form.gender} onChange={(e) => setForm((s) => ({ ...s, gender: e.target.value }))}>
            <option>Male</option>
            <option>Female</option>
          </Select>
        </div>
        <div className="space-y-2">
          <FieldLabel htmlFor="meal-goal">Goal</FieldLabel>
          <Select id="meal-goal" value={form.goal} onChange={(e) => setForm((s) => ({ ...s, goal: e.target.value }))}>
            <option>Gain Weight</option>
            <option>Loss fat</option>
            <option>Maintain weight</option>
            <option>Gain muscle</option>
            <option>Improve overall health</option>
          </Select>
        </div>
        <div className="space-y-2">
          <FieldLabel htmlFor="meal-diet">Diet Preference</FieldLabel>
          <Select
            id="meal-diet"
            value={form.diet_choice}
            onChange={(e) => setForm((s) => ({ ...s, diet_choice: e.target.value }))}
          >
            <option>Vegetarian</option>
            <option>Vegan</option>
            <option>Non-vegetarian</option>
            <option>Eggeterian</option>
          </Select>
        </div>
        <div className="space-y-2">
          <FieldLabel htmlFor="meal-issue">Health Consideration</FieldLabel>
          <Select id="meal-issue" value={form.issue} onChange={(e) => setForm((s) => ({ ...s, issue: e.target.value }))}>
            <option>No issue</option>
            <option>Lactose intolerant</option>
            <option>Gluten-free</option>
            <option>Nut allergy</option>
            <option>Other</option>
          </Select>
        </div>
        <div className="space-y-2">
          <FieldLabel htmlFor="meal-gym">Workout Frequency</FieldLabel>
          <Select id="meal-gym" value={form.gym} onChange={(e) => setForm((s) => ({ ...s, gym: e.target.value }))}>
            <option>do gym/workout</option>
            <option>do not gym/workout</option>
          </Select>
        </div>
        <div className="space-y-2">
          <FieldLabel htmlFor="meal-food-type">Cuisine Type</FieldLabel>
          <Select
            id="meal-food-type"
            value={form.food_type}
            onChange={(e) => setForm((s) => ({ ...s, food_type: e.target.value }))}
          >
            <option>Indian type</option>
            <option>Continental type</option>
            <option>World wide type</option>
          </Select>
        </div>
        <div className="space-y-2">
          <FieldLabel htmlFor="meal-height">Height</FieldLabel>
          <Input
            id="meal-height"
            placeholder="e.g., 180 cm"
            value={form.height}
            onChange={(e) => setForm((s) => ({ ...s, height: e.target.value }))}
          />
        </div>
        <div className="space-y-2">
          <FieldLabel htmlFor="meal-weight">Weight</FieldLabel>
          <Input
            id="meal-weight"
            placeholder="e.g., 69 kg"
            value={form.weight}
            onChange={(e) => setForm((s) => ({ ...s, weight: e.target.value }))}
          />
        </div>

        <div className="sm:col-span-2 pt-4">
          <Button type="submit" size="lg" className="w-full rounded-full bg-vibrant hover:bg-vibrant/90 text-white shadow-soft-glow" disabled={loading}>
            {loading ? "Generating..." : "Generate Meal Plan"}
          </Button>
        </div>
      </form>

      {error ? <Alert variant="error" className="mt-8 rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant">{error}</Alert> : null}

      {result ? (
        <div className="mt-12 space-y-8 animate-reveal">
          <ResultBlock title="Meal Plan">
            <div className="grid gap-6 md:grid-cols-2">
              {result.sections.map((section) => (
                <div key={section.name} className="rounded-editorial border border-black/[0.03] bg-white/40 p-6 shadow-soft-glow">
                  <p className="text-xs font-bold uppercase tracking-widest text-vibrant mb-4 border-b border-black/[0.03] pb-3">{section.name}</p>
                  <ul className="space-y-3 text-sm text-foreground/70 font-medium leading-relaxed">
                    {section.options.map((option, index) => (
                      <li key={`${section.name}-${index}`} className="flex items-start gap-3">
                        <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-vibrant/40 flex-shrink-0" />
                        {option}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </ResultBlock>

          <ResultBlock title="Export PDF" className="bg-vibrant/5 border-vibrant/10">
            <div className="grid gap-6 md:grid-cols-3 items-end">
              <div className="space-y-2">
                <FieldLabel htmlFor="meal-pdf-name">Name</FieldLabel>
                <Input id="meal-pdf-name" placeholder="Full name" className="bg-white/60 border-vibrant/20" value={pdfName} onChange={(e) => setPdfName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <FieldLabel htmlFor="meal-pdf-age">Age</FieldLabel>
                <Input
                  id="meal-pdf-age"
                  placeholder="Age"
                  type="number"
                  className="bg-white/60 border-vibrant/20"
                  value={pdfAge}
                  onChange={(e) => setPdfAge(Number(e.target.value || 0))}
                />
              </div>
              <div>
                <Button type="button" variant="primary" className="w-full rounded-full bg-foreground text-background" onClick={downloadPdf}>
                  Download PDF
                </Button>
              </div>
            </div>

            <div className="mt-6 border-t border-vibrant/10 pt-5">
              <p className="text-xs font-bold uppercase tracking-widest text-vibrant/70">Saved PDFs</p>
              {loadingExports ? (
                <p className="mt-3 text-sm text-foreground/40">Loading saved exports...</p>
              ) : savedExports.length ? (
                <div className="mt-4 space-y-3">
                  {savedExports.map((item) => (
                    <div
                      key={item.id}
                      className="flex flex-col gap-3 rounded-editorial border border-black/[0.03] bg-white/60 p-4 shadow-soft-glow md:flex-row md:items-center md:justify-between"
                    >
                      <div>
                        <p className="text-sm font-semibold text-foreground">{item.full_name} · Age {item.age}</p>
                        <p className="mt-1 text-[11px] font-bold uppercase tracking-widest text-foreground/35">
                          {new Date(item.created_at).toLocaleString()} · {Math.max(1, Math.round(item.byte_size / 1024))} KB
                        </p>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        className="rounded-full"
                        onClick={() => void downloadSavedPdf(item)}
                      >
                        Re-download
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-foreground/40">No saved PDFs yet for this meal plan.</p>
              )}
            </div>
          </ResultBlock>
        </div>
      ) : null}
    </FeatureShell>
  );
}
