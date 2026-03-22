"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useApiClient } from "@/hooks/useApiClient";
import type { Article } from "@/types/api";

export default function ArticleDetailPage() {
  const api = useApiClient();
  const params = useParams<{ slug: string }>();
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadArticle() {
      setLoading(true);
      setError(null);
      try {
        const row = await api.getArticle(params.slug);
        setArticle(row);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load article");
      } finally {
        setLoading(false);
      }
    }

    if (params.slug) {
      void loadArticle();
    }
  }, [api, params.slug]);

  return (
    <div className="bg-background pt-40 pb-20">
      <div className="mx-auto w-full max-w-[920px] px-6 sm:px-10">
        <div className="space-y-6">
          <Link href="/articles">
            <Button variant="ghost" size="sm">Back to articles</Button>
          </Link>

          {loading ? <div className="app-panel p-8 text-sm text-foreground/65">Loading article...</div> : null}
          {error ? <Alert variant="error">{error}</Alert> : null}

          {article ? (
            <article className="app-panel p-8">
              <div className="text-sm text-vibrant">Article</div>
              <h1 className="mt-4 text-5xl font-display leading-tight text-foreground">{article.title}</h1>
              <p className="mt-4 text-sm text-foreground/55">{new Date(article.created_at).toLocaleString()}</p>
              <div className="mt-8 whitespace-pre-wrap text-base leading-8 text-foreground/80">{article.content}</div>
            </article>
          ) : null}
        </div>
      </div>
    </div>
  );
}
