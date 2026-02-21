"use client";

import { FormEvent, useState } from "react";
import { useUser } from "@clerk/nextjs";

import { FeatureShell } from "@/components/features/feature-shell";
import { HistoryPanel } from "@/components/features/history-panel";
import { ResultBlock } from "@/components/features/result-block";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useApiClient } from "@/hooks/useApiClient";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { useConvexHistory } from "@/hooks/useConvexHistory";
import type { IngredientCheckResponse, InputMode } from "@/types/api";

export default function IngredientCheckerPage() {
  const api = useApiClient();
  const { user } = useUser();

  const [mode, setMode] = useState<InputMode>("text");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<IngredientCheckResponse | null>(null);

  const { data: history, loading: historyLoading, refreshInBackground } = useConvexHistory<IngredientCheckResponse>({
    functionName: "ingredientChecks:listByUser",
    clerkUserId: user?.id,
    limit: 20,
    pollIntervalMs: 25000,
  });

  const { execute, loading, error } = useAsyncAction(async () => {
    if (mode === "text") return api.analyzeIngredientsText(text);
    if (!file) throw new Error("Please upload an image before analyzing");
    return api.analyzeIngredientsImage(file);
  });

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const payload = await execute();
    if (payload) {
      setResult(payload);
      refreshInBackground();
    }
  }

  return (
    <FeatureShell
      title="Ingredient Checker"
      description="Evaluate ingredients and identify safer choices with potential health issue flags."
      aside={
        <HistoryPanel title="Recent Ingredient Checks" loading={historyLoading} empty={!history.length} syncing={loading}>
          {history.map((item) => (
            <button
              key={item.id}
              className="w-full rounded-xl border border-surface-200 bg-surface-50 p-3 text-left"
              onClick={() => setResult(item)}
            >
              <p className="text-sm font-semibold text-accent-800">{new Date(item.created_at).toLocaleString()}</p>
              <p className="mt-1 text-xs text-accent-600">
                Healthy: {item.healthy_ingredients.length} | Mindful: {item.unhealthy_ingredients.length}
              </p>
            </button>
          ))}
        </HistoryPanel>
      }
    >
      <div className="space-y-5">
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant={mode === "text" ? "primary" : "ghost"} onClick={() => setMode("text")}>
            Text Input
          </Button>
          <Button type="button" variant={mode === "image" ? "primary" : "ghost"} onClick={() => setMode("image")}>
            Image Upload
          </Button>
        </div>

        <form className="space-y-4" onSubmit={onSubmit}>
          {mode === "text" ? (
            <Textarea
              placeholder="Example: spinach, olive oil, sugar, trans fat"
              value={text}
              onChange={(event) => setText(event.target.value)}
            />
          ) : (
            <Input type="file" accept="image/png,image/jpg,image/jpeg,image/webp" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          )}

          <Button type="submit" disabled={loading}>
            {loading ? "Analyzing..." : "Analyze Ingredients"}
          </Button>
        </form>

        {error ? <Alert variant="error">{error}</Alert> : null}

        {result ? (
          <div className="space-y-4">
            <ResultBlock title="Safe Ingredients">
              <div className="flex flex-wrap gap-2">
                {result.healthy_ingredients.length ? (
                  result.healthy_ingredients.map((item) => (
                    <span key={item} className="rounded-full bg-success-50 px-3 py-1 text-xs font-semibold text-success-700">
                      {item}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-accent-600">No specific safe ingredients identified.</p>
                )}
              </div>
            </ResultBlock>

            <ResultBlock title="Ingredients To Be Mindful Of">
              <div className="flex flex-wrap gap-2">
                {result.unhealthy_ingredients.length ? (
                  result.unhealthy_ingredients.map((item) => (
                    <span key={item} className="rounded-full bg-warning-50 px-3 py-1 text-xs font-semibold text-warning-700">
                      {item}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-accent-600">No concerning ingredients identified.</p>
                )}
              </div>
            </ResultBlock>

            <ResultBlock title="Potential Health Concerns">
              {Object.keys(result.health_issues).length ? (
                <div className="space-y-2">
                  {Object.entries(result.health_issues).map(([ingredient, issues]) => (
                    <div key={ingredient} className="rounded-lg border border-danger-500/20 bg-danger-50 px-3 py-2">
                      <p className="text-sm font-semibold text-danger-700">{ingredient}</p>
                      <p className="text-xs text-danger-700">{issues.join(", ")}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-accent-600">No specific health concerns detected.</p>
              )}
            </ResultBlock>
          </div>
        ) : null}
      </div>
    </FeatureShell>
  );
}
