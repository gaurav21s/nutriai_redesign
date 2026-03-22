"use client";

import { FormEvent, useState } from "react";
import { useUser } from "@clerk/nextjs";
import { Sparkles, RefreshCcw, ArrowRight } from "lucide-react";

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
      description="Get healthier alternatives and new healthy ideas from your query."
      aside={
        <HistoryPanel title="Recent Insights" loading={historyLoading} empty={!history.length} syncing={loading}>
          {history.map((item) => (
            <button
              key={item.id}
              className="w-full rounded-editorial border border-black/[0.03] bg-white/40 backdrop-blur-sm p-4 text-left transition-all hover:border-vibrant/20 shadow-soft-glow group"
              onClick={() => setResult(item)}
            >
              <div className="flex items-center gap-3 mb-2">
                <RefreshCcw className="h-3.5 w-3.5 text-vibrant/40 group-hover:text-vibrant transition-colors" />
                <p className="text-sm font-semibold text-foreground group-hover:text-vibrant transition-colors truncate">{item.title}</p>
              </div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-foreground/30">{new Date(item.created_at).toLocaleString()}</p>
            </button>
          ))}
        </HistoryPanel>
      }
    >
      <form className="grid gap-6 sm:grid-cols-[1fr_240px_auto]" onSubmit={onSubmit}>
        <div className="space-y-2">
          <FieldLabel htmlFor="recommendation-query">Base Query</FieldLabel>
          <Input
            id="recommendation-query"
            placeholder="e.g., late-night snack ideas or office lunch alternatives"
            className="bg-white/50 border-black/[0.05] focus:border-vibrant transition-all"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <FieldLabel htmlFor="recommendation-type">Recommendation Type</FieldLabel>
          <Select
            id="recommendation-type"
            value={type}
            className="bg-white/50 border-black/[0.05] focus:border-vibrant transition-all"
            onChange={(e) => setType(e.target.value as RecommendationType)}
          >
            <option value="both">Both</option>
            <option value="healthier_alternative">Healthier alternatives</option>
            <option value="new_healthy_recipe">New healthy recipe</option>
          </Select>
        </div>
        <div className="pt-[22px]">
          <Button type="submit" size="lg" className="rounded-full bg-vibrant hover:bg-vibrant/90 text-white shadow-soft-glow px-10" disabled={loading}>
            {loading ? "Generating..." : "Get Recommendations"}
          </Button>
        </div>
      </form>

      {error ? <Alert variant="error" className="mt-8 rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant">{error}</Alert> : null}

      {result ? (
        <div className="mt-12 animate-reveal">
          <ResultBlock title={result.title}>
            <ul className="grid gap-4 md:grid-cols-2">
              {result.recommendations.map((item, index) => (
                <li key={`${item}-${index}`} className="rounded-editorial border border-black/[0.03] bg-white/40 p-6 shadow-soft-glow flex gap-4 group hover:border-vibrant/20 transition-all">
                  <span className="text-vibrant font-display italic text-2xl leading-none">0{index + 1}.</span>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-foreground/80 leading-relaxed group-hover:text-foreground transition-colors">
                      {item}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-vibrant opacity-0 group-hover:opacity-100 transition-opacity">
                      View Details <ArrowRight className="h-3 w-3" />
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </ResultBlock>
        </div>
      ) : null}
    </FeatureShell>
  );
}
