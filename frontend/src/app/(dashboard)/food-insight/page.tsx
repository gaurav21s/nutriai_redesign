"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { Sparkles, Activity, PieChart, Info, ArrowRight } from "lucide-react";

import { FeatureShell } from "@/components/features/feature-shell";
import { HistoryPanel } from "@/components/features/history-panel";
import { ResultBlock } from "@/components/features/result-block";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FieldLabel } from "@/components/ui/field-label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useApiClient } from "@/hooks/useApiClient";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { useConvexHistory } from "@/hooks/useConvexHistory";
import type { FoodInsightResponse, InputMode } from "@/types/api";

function FoodInsightPageContent() {
  const api = useApiClient();
  const { user } = useUser();

  const searchParams = useSearchParams();
  const [mode, setMode] = useState<InputMode>("text");
  const [text, setText] = useState("");

  useEffect(() => {
    const q = searchParams.get("text");
    if (q) { setMode("text"); setText(q); }
  }, [searchParams]);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<FoodInsightResponse | null>(null);

  const { data: history, loading: historyLoading, refreshInBackground } = useConvexHistory<FoodInsightResponse>({
    functionName: "foodInsights:listByUser",
    clerkUserId: user?.id,
    limit: 20,
    pollIntervalMs: 25000,
  });

  const { execute, loading, error } = useAsyncAction(async () => {
    if (mode === "text") return api.analyzeFoodText(text);
    if (!file) throw new Error("Please upload an image before analyzing");
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
      description="Analyze your meal from text or image and get a clear nutrition summary."
      aside={
        <HistoryPanel title="Recent Activity" loading={historyLoading} empty={!history.length} syncing={loading}>
          {history.map((item) => (
            <button
              key={item.id}
              className="w-full rounded-editorial border border-black/[0.03] bg-white/40 backdrop-blur-sm p-4 text-left transition-all hover:border-vibrant/20 shadow-soft-glow group"
              onClick={() => setResult(item)}
            >
              <div className="flex items-center gap-3 mb-2">
                <Activity className="h-3.5 w-3.5 text-vibrant/40 group-hover:text-vibrant transition-colors" />
                <p className="text-sm font-semibold text-foreground group-hover:text-vibrant transition-colors truncate">{new Date(item.created_at).toLocaleTimeString()}</p>
              </div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-foreground/30">{item.verdict}</p>
            </button>
          ))}
        </HistoryPanel>
      }
    >
      <div className="space-y-8">
        <div className="flex p-1 bg-black/[0.03] rounded-full w-fit">
          <button
            type="button"
            className={`px-6 py-2 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all ${mode === "text" ? "bg-white shadow-soft-glow text-foreground" : "text-foreground/40 hover:text-foreground/60"
              }`}
            onClick={() => setMode("text")}
          >
            Text Input
          </button>
          <button
            type="button"
            className={`px-6 py-2 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all ${mode === "image" ? "bg-white shadow-soft-glow text-foreground" : "text-foreground/40 hover:text-foreground/60"
              }`}
            onClick={() => setMode("image")}
          >
            Image Input
          </button>
        </div>

        <form className="space-y-6" onSubmit={onSubmit}>
          {mode === "text" ? (
            <div className="space-y-2">
              <FieldLabel htmlFor="food-text">What did you eat?</FieldLabel>
              <Textarea
                id="food-text"
                placeholder="Example: 2 slices of pizza, 1 apple, 200ml yogurt"
                className="h-32 bg-white/50 border-black/[0.05] focus:border-vibrant transition-all"
                value={text}
                onChange={(event) => setText(event.target.value)}
              />
            </div>
          ) : (
            <div className="space-y-2">
              <FieldLabel htmlFor="food-image">Upload meal image</FieldLabel>
              <div className="relative group">
                <Input
                  id="food-image"
                  type="file"
                  className="h-32 rounded-editorial border-dashed border-black/[0.1] bg-black/[0.01] hover:bg-black/[0.02] transition-all flex items-center justify-center text-center cursor-pointer"
                  accept="image/png,image/jpg,image/jpeg,image/webp"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                />
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-foreground/30 group-hover:text-vibrant/60 transition-colors">
                  <Sparkles className="h-6 w-6 mb-2" />
                  <p className="text-xs font-semibold uppercase tracking-widest">{file ? file.name : "Drop or click to upload"}</p>
                </div>
              </div>
            </div>
          )}

          <Button type="submit" size="lg" className="rounded-full bg-vibrant hover:bg-vibrant/90 text-white shadow-soft-glow px-12" disabled={loading}>
            {loading ? "Analyzing..." : "Analyze Food"}
          </Button>
        </form>

        {error ? <Alert variant="error" className="rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant">{error}</Alert> : null}

        {result ? (
          <div className="space-y-6 animate-reveal">
            <ResultBlock title="Overall Result">
              <div className="flex items-center gap-4">
                <Badge className="bg-vibrant text-white rounded-full px-6 py-2 text-[10px] uppercase font-bold tracking-widest border-none shadow-soft-glow">{result.verdict}</Badge>
                <div className="h-[1px] flex-1 bg-black/[0.05]" />
              </div>
            </ResultBlock>

            <ResultBlock title="Nutrition Totals" className="bg-black/[0.01]">
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
                {Object.entries(result.totals).map(([key, value]) => (
                  <div key={key} className="rounded-editorial border border-black/[0.03] bg-white/60 p-5 shadow-soft-glow group hover:border-vibrant/20 transition-all">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-foreground/30 mb-2 truncate">{key}</p>
                    <p className="text-xl font-display font-semibold text-foreground group-hover:text-vibrant transition-colors">{value ?? "0"}</p>
                  </div>
                ))}
              </div>
            </ResultBlock>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <ResultBlock title="Detected Items" className="mt-0">
                <div className="space-y-3">
                  {result.items.map((item, index) => (
                    <div key={`${item.name}-${index}`} className="rounded-editorial border border-black/[0.03] bg-white/40 p-4 shadow-soft-glow transition-all hover:bg-white/60">
                      <p className="text-sm font-bold text-foreground mb-1">{item.name}</p>
                      <p className="text-xs text-foreground/50 font-medium italic">{item.details ?? "No extra details"}</p>
                    </div>
                  ))}
                </div>
              </ResultBlock>

              <ResultBlock title="Key Facts" className="mt-0">
                <ul className="space-y-3">
                  {result.facts.map((fact, index) => (
                    <li key={`${fact}-${index}`} className="rounded-editorial border border-black/[0.03] bg-black/[0.03] px-5 py-4 text-xs font-medium text-foreground/70 leading-relaxed relative overflow-hidden group">
                      <div className="absolute top-0 left-0 bottom-0 w-1 bg-vibrant/20 group-hover:bg-vibrant transition-colors" />
                      {fact}
                    </li>
                  ))}
                </ul>
              </ResultBlock>
            </div>
          </div>
        ) : null}
      </div>
    </FeatureShell>
  );
}

export default function FoodInsightPage() {
  return (
    <Suspense fallback={null}>
      <FoodInsightPageContent />
    </Suspense>
  );
}
