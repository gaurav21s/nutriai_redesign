"use client";

import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useApiClient } from "@/hooks/useApiClient";
import type { Article } from "@/types/api";

export default function ArticlesPage() {
  const api = useApiClient();

  const [query, setQuery] = useState("");
  const [articles, setArticles] = useState<Article[]>([]);
  const [selected, setSelected] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadArticles(search?: string) {
    setLoading(true);
    setError(null);
    try {
      const rows = await api.listArticles(search);
      setArticles(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load articles");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadArticles();
  }, []);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>NutriAI Articles</CardTitle>
          <p className="text-sm text-accent-600">Search, browse, and read curated nutrition content.</p>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Input placeholder="Search title or summary" value={query} onChange={(e) => setQuery(e.target.value)} />
            <Button type="button" onClick={() => void loadArticles(query)}>
              Search
            </Button>
          </div>
        </CardContent>
      </Card>

      {error ? <Alert variant="error">{error}</Alert> : null}

      <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>All Articles</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-sm text-accent-600">Loading articles...</p>
            ) : !articles.length ? (
              <p className="text-sm text-accent-600">No articles found.</p>
            ) : (
              <div className="space-y-3">
                {articles.map((article) => (
                  <button
                    key={article.id}
                    className="w-full rounded-xl border border-surface-200 p-3 text-left hover:border-brand-300"
                    onClick={() => setSelected(article)}
                  >
                    <p className="text-sm font-semibold text-accent-900">{article.title}</p>
                    <p className="mt-1 text-xs text-accent-600">{article.summary}</p>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{selected ? selected.title : "Article Preview"}</CardTitle>
          </CardHeader>
          <CardContent>
            {selected ? (
              <article className="prose prose-sm max-w-none whitespace-pre-wrap text-accent-700">{selected.content}</article>
            ) : (
              <p className="text-sm text-accent-600">Select an article to read full content.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
