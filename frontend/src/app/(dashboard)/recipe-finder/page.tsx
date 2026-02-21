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
import type { RecipeResponse, RecipeType, ShoppingLinksResponse } from "@/types/api";

export default function RecipeFinderPage() {
  const api = useApiClient();
  const { user } = useUser();

  const [dishName, setDishName] = useState("");
  const [recipeType, setRecipeType] = useState<RecipeType>("normal");
  const [recipe, setRecipe] = useState<RecipeResponse | null>(null);
  const [links, setLinks] = useState<ShoppingLinksResponse | null>(null);

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
    refreshInBackground();
    const shopping = await api.getShoppingLinks(payload.ingredient_list);
    setLinks(shopping);
  }

  return (
    <FeatureShell
      title="Recipe Finder"
      description="Generate recipes, compare healthier variants, and open shopping links instantly."
      aside={
        <HistoryPanel title="Recent Recipes" loading={historyLoading} empty={!history.length} syncing={loading}>
          {history.map((item) => (
            <button
              key={item.id}
              className="w-full rounded-xl border border-surface-200 bg-surface-50 p-3 text-left"
              onClick={() => setRecipe(item)}
            >
              <p className="text-sm font-semibold text-accent-800">{item.recipe_name}</p>
              <p className="mt-1 text-xs text-accent-600">{new Date(item.created_at).toLocaleString()}</p>
            </button>
          ))}
        </HistoryPanel>
      }
    >
      <form className="grid gap-3 sm:grid-cols-[1fr_220px_auto]" onSubmit={onSubmit}>
        <Input
          placeholder="Dish name or cuisine"
          value={dishName}
          onChange={(event) => setDishName(event.target.value)}
        />
        <Select value={recipeType} onChange={(event) => setRecipeType(event.target.value as RecipeType)}>
          <option value="normal">Normal</option>
          <option value="healthier">Healthier alternative</option>
          <option value="new_healthy">New healthy and trendy recipe</option>
        </Select>
        <Button type="submit" disabled={loading}>
          {loading ? "Generating..." : "Generate"}
        </Button>
      </form>

      {error ? <Alert variant="error">{error}</Alert> : null}

      {recipe ? (
        <div className="mt-6 space-y-4">
          <ResultBlock title={recipe.recipe_name}>
            <div className="space-y-4">
              <div>
                <p className="mb-2 text-sm font-semibold text-accent-800">Ingredients</p>
                <ul className="space-y-1 text-sm text-accent-700">
                  {recipe.ingredients.map((item, index) => (
                    <li key={`${item.raw}-${index}`}>{item.raw}</li>
                  ))}
                </ul>
              </div>

              <div>
                <p className="mb-2 text-sm font-semibold text-accent-800">Steps</p>
                <ol className="space-y-1 text-sm text-accent-700">
                  {recipe.steps.map((step, index) => (
                    <li key={`${step}-${index}`}>{`${index + 1}. ${step}`}</li>
                  ))}
                </ol>
              </div>

              {recipe.explanation ? <Alert variant="info">{recipe.explanation}</Alert> : null}
            </div>
          </ResultBlock>

          {links ? (
            <ResultBlock title="Shopping Links">
              <div className="grid gap-2 sm:grid-cols-2">
                {Object.entries(links.links).map(([ingredient, pair]) => (
                  <div key={ingredient} className="rounded-lg border border-surface-200 p-3">
                    <p className="text-sm font-semibold text-accent-800">{ingredient}</p>
                    <div className="mt-2 flex gap-3 text-sm text-accent-700">
                      <a href={pair.amazon} target="_blank" rel="noreferrer" className="underline">
                        Amazon
                      </a>
                      <a href={pair.blinkit} target="_blank" rel="noreferrer" className="underline">
                        Blinkit
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </ResultBlock>
          ) : null}
        </div>
      ) : null}
    </FeatureShell>
  );
}
