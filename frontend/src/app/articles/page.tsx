"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FieldLabel } from "@/components/ui/field-label";
import { Input } from "@/components/ui/input";
import { useApiClient } from "@/hooks/useApiClient";
import type { Article } from "@/types/api";

export default function ArticlesPage() {
  const api = useApiClient();
  const [query, setQuery] = useState("");
  const [articles, setArticles] = useState<Article[]>([]);
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
    <div className="bg-background pt-40 pb-20">
      <div className="mx-auto w-full max-w-[1440px] px-6 sm:px-10 lg:px-16">
        <div className="space-y-10">
          <header className="grid gap-8 border-b border-black/[0.08] pb-8 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-end">
            <div>
              <h1 className="text-6xl sm:text-7xl font-display leading-[0.95] text-foreground">
                Read <span className="italic text-vibrant">Articles</span>
              </h1>
              <p className="mt-6 max-w-2xl text-xl leading-relaxed text-foreground/60">
                Browse practical reading on food, fitness, meal planning, and everyday nutrition habits.
              </p>
            </div>

            <section className="app-panel p-6">
              <FieldLabel htmlFor="article-search">Search articles</FieldLabel>
              <div className="mt-2 flex gap-3">
                <div className="relative flex-1">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
                  <Input
                    id="article-search"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Title or topic"
                    className="pl-10"
                  />
                </div>
                <Button type="button" onClick={() => void loadArticles(query)}>
                  Search
                </Button>
              </div>
            </section>
          </header>

          {error ? <Alert variant="error">{error}</Alert> : null}

          {loading ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((item) => (
                <div key={item} className="app-panel h-56 animate-pulse" />
              ))}
            </div>
          ) : !articles.length ? (
            <div className="app-panel p-8 text-sm text-foreground/65">No articles found.</div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {articles.map((article) => (
                <Link key={article.id} href={`/articles/${article.slug}`} className="app-panel p-7 hover:bg-muted">
                  <div className="text-xs text-vibrant">Article</div>
                  <h2 className="mt-5 text-3xl font-display leading-tight text-foreground">{article.title}</h2>
                  <p className="mt-4 text-sm leading-6 text-foreground/70">{article.summary}</p>
                  <div className="mt-8 text-sm text-[rgb(180,83,9)]">Open article</div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
