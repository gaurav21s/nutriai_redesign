"use client";

import { FormEvent, useState } from "react";
import { useUser } from "@clerk/nextjs";

import { FeatureShell } from "@/components/features/feature-shell";
import { HistoryPanel } from "@/components/features/history-panel";
import { ResultBlock } from "@/components/features/result-block";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useApiClient } from "@/hooks/useApiClient";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { useConvexHistory } from "@/hooks/useConvexHistory";
import type { FoodInsightResponse, InputMode } from "@/types/api";

export default function FoodInsightPage() {
  const api = useApiClient();
  const { user } = useUser();

  const [mode, setMode] = useState<InputMode>("text");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<FoodInsightResponse | null>(null);

  const { data: history, loading: historyLoading, refreshInBackground } = useConvexHistory<FoodInsightResponse>({
    functionName: "foodInsights:listByUser",
    clerkUserId: user?.id,
    limit: 20,
    pollIntervalMs: 25000,
  });

  const { execute, loading, error } = useAsyncAction(async () => {
    if (mode === "text") {
      return api.analyzeFoodText(text);
    }
    if (!file) {
      throw new Error("Please upload an image before analyzing");
    }
    return api.analyzeFoodImage(file);
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
      title="Food Insight"
      description="Analyze food items from text or image and receive structured nutrition summaries."
      aside={
        <HistoryPanel title="Recent Analyses" loading={historyLoading} empty={!history.length} syncing={loading}>
          {history.map((item) => (
            <button
              key={item.id}
              className="w-full rounded-xl border border-surface-200 bg-surface-50 p-3 text-left hover:border-brand-300"
              onClick={() => setResult(item)}
            >
              <p className="text-sm font-semibold text-accent-800">{new Date(item.created_at).toLocaleString()}</p>
              <p className="mt-1 text-sm text-accent-600">{item.verdict}</p>
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
              placeholder="Example: 2 slices of pizza, 1 apple, 200ml yogurt"
              value={text}
              onChange={(event) => setText(event.target.value)}
            />
          ) : (
            <Input type="file" accept="image/png,image/jpg,image/jpeg,image/webp" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          )}

          <Button type="submit" disabled={loading}>
            {loading ? "Analyzing..." : "Analyze Food"}
          </Button>
        </form>

        {error ? <Alert variant="error">{error}</Alert> : null}

        {result ? (
          <div className="space-y-4">
            <ResultBlock title="Verdict">
              <Badge>{result.verdict}</Badge>
            </ResultBlock>

            <ResultBlock title="Nutrition Totals">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                {Object.entries(result.totals).map(([key, value]) => (
                  <div key={key} className="rounded-lg border border-surface-200 bg-surface-50 px-3 py-2">
                    <p className="text-xs uppercase tracking-wide text-accent-500">{key}</p>
                    <p className="text-sm font-semibold text-accent-800">{value ?? "N/A"}</p>
                  </div>
                ))}
              </div>
            </ResultBlock>

            <ResultBlock title="Items">
              <div className="space-y-2">
                {result.items.map((item, index) => (
                  <div key={`${item.name}-${index}`} className="rounded-lg border border-surface-200 px-3 py-2">
                    <p className="text-sm font-semibold text-accent-800">{item.name}</p>
                    <p className="text-xs text-accent-600">{item.details ?? "No details available"}</p>
                  </div>
                ))}
              </div>
            </ResultBlock>

            <ResultBlock title="Facts">
              <ul className="space-y-2 text-sm text-accent-700">
                {result.facts.map((fact, index) => (
                  <li key={`${fact}-${index}`} className="rounded-lg bg-surface-100 px-3 py-2">
                    {fact}
                  </li>
                ))}
              </ul>
            </ResultBlock>
          </div>
        ) : null}
      </div>
    </FeatureShell>
  );
}
