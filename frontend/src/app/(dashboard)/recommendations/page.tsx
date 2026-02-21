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
import type { RecommendationResponse, RecommendationType } from "@/types/api";

export default function RecommendationsPage() {
  const api = useApiClient();
  const { user } = useUser();

  const [query, setQuery] = useState("");
  const [type, setType] = useState<RecommendationType>("both");
  const [result, setResult] = useState<RecommendationResponse | null>(null);

  const { data: history, loading: historyLoading, refreshInBackground } = useConvexHistory<RecommendationResponse>({
    functionName: "recommendations:listByUser",
    clerkUserId: user?.id,
    limit: 20,
    pollIntervalMs: 25000,
  });

  const { execute, loading, error } = useAsyncAction(async () => api.generateRecommendations(query, type));

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
      title="Recommendations"
      description="Generate healthier alternatives and fresh healthy recipe suggestions from any query."
      aside={
        <HistoryPanel title="Recent Recommendations" loading={historyLoading} empty={!history.length} syncing={loading}>
          {history.map((item) => (
            <button
              key={item.id}
              className="w-full rounded-xl border border-surface-200 bg-surface-50 p-3 text-left"
              onClick={() => setResult(item)}
            >
              <p className="text-sm font-semibold text-accent-800">{item.title}</p>
              <p className="mt-1 text-xs text-accent-600">{new Date(item.created_at).toLocaleString()}</p>
            </button>
          ))}
        </HistoryPanel>
      }
    >
      <form className="grid gap-3 sm:grid-cols-[1fr_220px_auto]" onSubmit={onSubmit}>
        <Input placeholder="Example: late-night snack ideas" value={query} onChange={(e) => setQuery(e.target.value)} />
        <Select value={type} onChange={(e) => setType(e.target.value as RecommendationType)}>
          <option value="both">Both</option>
          <option value="healthier_alternative">Healthier alternatives</option>
          <option value="new_healthy_recipe">New healthy recipe</option>
        </Select>
        <Button type="submit" disabled={loading}>
          {loading ? "Generating..." : "Generate"}
        </Button>
      </form>

      {error ? <Alert variant="error">{error}</Alert> : null}

      {result ? (
        <ResultBlock title={result.title}>
          <ul className="space-y-2 text-sm text-accent-700">
            {result.recommendations.map((item, index) => (
              <li key={`${item}-${index}`} className="rounded-lg border border-surface-200 bg-surface-50 px-3 py-2">
                {item}
              </li>
            ))}
          </ul>
        </ResultBlock>
      ) : null}
    </FeatureShell>
  );
}
