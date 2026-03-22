"use client";

import { FormEvent, useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";
import { Sparkles, Utensils } from "lucide-react";

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
import type { RecipeResponse, RecipeType, ShoppingLinkPair } from "@/types/api";

function normalizeIngredientName(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/^[\d\s/.,-]+(?:cups?|cup|tbsp|tablespoons?|tsp|teaspoons?|grams?|gram|g|kg|ml|l|oz|ounces?|lb|pounds?|pinch)\b/i, "")
    .replace(/^of\s+/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

function getIngredientLinks(
  recipe: RecipeResponse,
  ingredientRaw: string,
  fallbackLinks: Record<string, ShoppingLinkPair>
): ShoppingLinkPair | null {
  const normalized = normalizeIngredientName(ingredientRaw);
  const linkEntries = Object.entries({
    ...(recipe.shopping_links ?? {}),
    ...fallbackLinks,
  });
    const exactMatch = linkEntries.find(([name]) => name.trim().toLowerCase() === normalized);
  if (exactMatch) {
    return exactMatch[1];
  }

  const looseMatch = linkEntries.find(([name]) => {
    const candidate = normalizeIngredientName(name);
    return normalized.includes(candidate) || candidate.includes(normalized);
  });
  return looseMatch ? looseMatch[1] : null;
}

function StoreAction({
  href,
  label,
  iconSrc,
}: {
  href: string;
  label: string;
  iconSrc: string;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-black/[0.08] bg-white/95 transition-all hover:-translate-y-0.5 hover:border-vibrant/30 hover:shadow-soft-glow"
      aria-label={`Buy ${label}`}
      title={label}
    >
      <img src={iconSrc} alt="" aria-hidden="true" className="h-4 w-4 rounded-[4px] object-contain" />
    </a>
  );
}

export default function RecipeFinderPage() {
  const api = useApiClient();
  const { user } = useUser();

  const [dishName, setDishName] = useState("");
  const [recipeType, setRecipeType] = useState<RecipeType>("normal");
  const [recipe, setRecipe] = useState<RecipeResponse | null>(null);
  const [fallbackLinks, setFallbackLinks] = useState<Record<string, ShoppingLinkPair>>({});
  const [linksLoading, setLinksLoading] = useState(false);

  const { data: history, loading: historyLoading, refreshInBackground } = useConvexHistory<RecipeResponse>({
    functionName: "recipes:listByUser",
    clerkUserId: user?.id,
    limit: 20,
    pollIntervalMs: 25000,
  });

  const { execute, loading, error } = useAsyncAction(async () => api.generateRecipe(dishName, recipeType));

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const payload = await execute();
    if (!payload) return;
    setRecipe(payload);
    setFallbackLinks({});
    refreshInBackground();
  }

  useEffect(() => {
    let cancelled = false;

    async function ensureLinks() {
      if (!recipe) {
        setFallbackLinks({});
        return;
      }

      const visibleIngredients = Array.from(
        new Set(
          recipe.ingredients
            .map((item) => normalizeIngredientName(item.raw))
            .filter(Boolean)
        )
      );

      const storedLinks = recipe.shopping_links ?? {};
      const missingVisibleLinks = visibleIngredients.some((ingredient) => {
        return !Object.keys(storedLinks).some((key) => normalizeIngredientName(key) === ingredient);
      });

      if (!missingVisibleLinks) {
        setFallbackLinks({});
        setLinksLoading(false);
        return;
      }

      setLinksLoading(true);
      try {
        const payload = await api.getShoppingLinks(visibleIngredients);
        if (!cancelled) {
          setFallbackLinks(payload.links);
        }
      } catch {
        if (!cancelled) {
          setFallbackLinks({});
        }
      } finally {
        if (!cancelled) {
          setLinksLoading(false);
        }
      }
    }

    void ensureLinks();

    return () => {
      cancelled = true;
    };
  }, [api, recipe]);

  return (
    <FeatureShell
      title="Recipe Finder"
      description="Generate recipes, compare healthier options, and get ingredient shopping links."
      aside={
        <HistoryPanel title="Recent Recipes" loading={historyLoading} empty={!history.length} syncing={loading}>
          {history.map((item) => (
            <button
              key={item.id}
              className="w-full rounded-editorial border border-black/[0.03] bg-white/40 backdrop-blur-sm p-4 text-left transition-all hover:border-vibrant/20 shadow-soft-glow group"
              onClick={() => setRecipe(item)}
            >
              <div className="flex items-center gap-3 mb-2">
                <Utensils className="h-3.5 w-3.5 text-vibrant/40 group-hover:text-vibrant transition-colors" />
                <p className="text-sm font-semibold text-foreground group-hover:text-vibrant transition-colors truncate">{item.recipe_name}</p>
              </div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-foreground/30">{new Date(item.created_at).toLocaleString()}</p>
            </button>
          ))}
        </HistoryPanel>
      }
    >
      <form className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-[minmax(0,1.35fr)_minmax(260px,0.75fr)_auto] xl:items-end" onSubmit={onSubmit}>
        <div className="space-y-2">
          <FieldLabel htmlFor="recipe-dish">Dish or cuisine</FieldLabel>
          <Input
            id="recipe-dish"
            placeholder="e.g., Mediterranean Salmon or Thai Green Curry"
            className="h-16 bg-white/50 border-black/[0.05] px-5 text-lg focus:border-vibrant transition-all"
            value={dishName}
            onChange={(event) => setDishName(event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <FieldLabel htmlFor="recipe-type">Recipe type</FieldLabel>
          <Select
            id="recipe-type"
            value={recipeType}
            className="h-16 bg-white/50 border-black/[0.05] px-5 text-lg focus:border-vibrant transition-all"
            onChange={(event) => setRecipeType(event.target.value as RecipeType)}
          >
            <option value="normal">Standard</option>
            <option value="healthier">Healthier option</option>
            <option value="new_healthy">New healthy recipe</option>
          </Select>
        </div>
        <div className="md:col-span-2 xl:col-span-1">
          <Button
            type="submit"
            size="lg"
            className="h-16 w-full rounded-full bg-vibrant px-8 text-lg text-white shadow-soft-glow hover:bg-vibrant/90 xl:min-w-[260px]"
            disabled={loading}
          >
            {loading ? "Generating..." : "Generate Recipe"}
          </Button>
        </div>
      </form>

      {error ? <Alert variant="error" className="mt-8 rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant">{error}</Alert> : null}

      {recipe ? (
        <div className="mt-12 space-y-8 animate-reveal">
          <ResultBlock title={recipe.recipe_name}>
            <div className="grid gap-8 xl:grid-cols-[minmax(280px,340px)_minmax(0,1fr)] xl:gap-10">
              <div className="space-y-6">
                <div>
                  <p className="mb-4 text-xs font-bold uppercase tracking-widest text-vibrant flex items-center gap-2">
                    <Sparkles className="h-3 w-3" />
                    Ingredients
                  </p>
                  <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1 text-sm text-foreground/70 font-medium italic">
                    {recipe.ingredients.map((item, index) => (
                      <li
                        key={`${item.raw}-${index}`}
                        className="rounded-2xl border border-black/[0.04] bg-white/55 px-4 py-4 shadow-soft-glow"
                      >
                        <div className="flex items-start gap-3">
                          <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-vibrant/30 flex-shrink-0" />
                          <div className="min-w-0 flex-1 space-y-3">
                            <p className="text-base leading-8 text-foreground/82 xl:text-[15px] xl:leading-8">{item.raw}</p>
                            {(() => {
                              const ingredientLinks = getIngredientLinks(recipe, item.raw, fallbackLinks);
                              if (!ingredientLinks) {
                                return linksLoading ? (
                                  <p className="not-italic text-[11px] font-semibold uppercase tracking-[0.18em] text-foreground/35">
                                    Finding product links...
                                  </p>
                                ) : null;
                              }

                              return (
                                <div className="flex items-center gap-2 not-italic">
                                  <StoreAction
                                    href={ingredientLinks.amazon}
                                    label="Amazon"
                                    iconSrc="/images/store/amazon.ico"
                                  />
                                  <StoreAction
                                    href={ingredientLinks.blinkit}
                                    label="Blinkit"
                                    iconSrc="/images/store/blinkit.ico"
                                  />
                                </div>
                              );
                            })()}
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <p className="mb-4 text-xs font-bold uppercase tracking-widest text-foreground/40 border-b border-black/[0.03] pb-2">Steps</p>
                  <ol className="space-y-4 text-base text-foreground/80 font-medium leading-9">
                    {recipe.steps.map((step, index) => (
                      <li key={`${step}-${index}`} className="flex gap-4">
                        <span className="mt-0.5 text-vibrant font-display italic text-2xl leading-none">{index + 1}.</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>

                {recipe.explanation ? (
                  <Alert variant="info" className="bg-vibrant/5 border-vibrant/10 rounded-2xl text-foreground font-medium italic">
                    {recipe.explanation}
                  </Alert>
                ) : null}
              </div>
            </div>
          </ResultBlock>
        </div>
      ) : null}
    </FeatureShell>
  );
}
