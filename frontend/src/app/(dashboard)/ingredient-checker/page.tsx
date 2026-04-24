"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { Sparkles, ShieldCheck, AlertCircle } from "lucide-react";

import { FeatureShell } from "@/components/features/feature-shell";
import { HistoryPanel } from "@/components/features/history-panel";
import { ResultBlock } from "@/components/features/result-block";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FieldLabel } from "@/components/ui/field-label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useApiClient } from "@/hooks/useApiClient";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { useConvexHistory } from "@/hooks/useConvexHistory";
import type { IngredientCheckResponse, InputMode } from "@/types/api";

function IngredientCheckerPageContent() {
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
      description="Check ingredients and see what is good, what is risky, and why."
      aside={
        <HistoryPanel title="Recent Analysis" loading={historyLoading} empty={!history.length} syncing={loading}>
          {history.map((item) => (
            <button
              key={item.id}
              className="w-full rounded-editorial border border-black/[0.03] bg-white/40 backdrop-blur-sm p-4 text-left transition-all hover:border-vibrant/20 shadow-soft-glow group"
              onClick={() => setResult(item)}
            >
              <p className="text-sm font-semibold text-foreground group-hover:text-vibrant transition-colors">{new Date(item.created_at).toLocaleString()}</p>
              <div className="mt-2 flex gap-3 text-[9px] font-bold uppercase tracking-widest">
                <span className="text-success-600">Good: {item.healthy_ingredients.length}</span>
                <span className="text-vibrant">Risky: {item.unhealthy_ingredients.length}</span>
              </div>
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
              <FieldLabel htmlFor="ingredient-text">Ingredients list</FieldLabel>
              <Textarea
                id="ingredient-text"
                placeholder="Example: spinach, olive oil, sugar, trans fat"
                className="h-32 bg-white/50 border-black/[0.05] focus:border-vibrant transition-all"
                value={text}
                onChange={(event) => setText(event.target.value)}
              />
            </div>
          ) : (
            <div className="space-y-2">
              <FieldLabel htmlFor="ingredient-image">Upload ingredient label image</FieldLabel>
              <div className="relative group">
                <Input
                  id="ingredient-image"
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
            {loading ? "Analyzing..." : "Analyze Ingredients"}
          </Button>
        </form>

        {error ? <Alert variant="error" className="rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant">{error}</Alert> : null}

        {result ? (
          <div className="space-y-6 animate-reveal">
            <ResultBlock title="Good Ingredients" className="bg-success-50/10 border-success-500/10">
              <div className="flex flex-wrap gap-2">
                {result.healthy_ingredients.length ? (
                  result.healthy_ingredients.map((item) => (
                    <span key={item} className="rounded-full bg-success-500 border border-success-500/20 px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest text-white shadow-sm">
                      {item}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-foreground/30 italic">No clearly healthy ingredients found.</p>
                )}
              </div>
            </ResultBlock>

            <ResultBlock title="Ingredients To Limit" className="bg-vibrant/5 border-vibrant/10">
              <div className="flex flex-wrap gap-2">
                {result.unhealthy_ingredients.length ? (
                  result.unhealthy_ingredients.map((item) => (
                    <span key={item} className="rounded-full bg-vibrant px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest text-white shadow-sm">
                      {item}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-foreground/30 italic">No high-risk ingredients found.</p>
                )}
              </div>
            </ResultBlock>

            <ResultBlock title="Health Notes">
              {Object.keys(result.health_issues).length ? (
                <div className="space-y-4">
                  {Object.entries(result.health_issues).map(([ingredient, issues]) => (
                    <div key={ingredient} className="rounded-editorial border border-black/[0.03] bg-white/40 p-5 shadow-soft-glow flex items-start gap-4">
                      <div className="mt-1 h-8 w-8 flex items-center justify-center rounded-full bg-vibrant/10 text-vibrant">
                        <AlertCircle className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-foreground mb-1">{ingredient}</p>
                        <p className="text-xs text-foreground/50 font-medium italic">{issues.join(" • ")}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center gap-4 text-success-600 italic">
                  <ShieldCheck className="h-5 w-5" />
                  <p className="text-sm font-medium">No health flags detected.</p>
                </div>
              )}
            </ResultBlock>
          </div>
        ) : null}
      </div>
    </FeatureShell>
  );
}

export default function IngredientCheckerPage() {
  return (
    <Suspense fallback={null}>
      <IngredientCheckerPageContent />
    </Suspense>
  );
}
