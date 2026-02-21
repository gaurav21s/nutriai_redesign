"""Service layer for articles."""

from __future__ import annotations

from pathlib import Path

from app.repositories.base import CompositeRepository
from app.schemas.articles import Article
from app.utils.legacy_articles import load_legacy_articles


class ArticleService:
    def __init__(self, repository: CompositeRepository, project_root: Path) -> None:
        self.repository = repository
        self.project_root = project_root

    async def _ensure_seeded(self) -> None:
        existing = await self.repository.list_articles(limit=1)
        if existing:
            return
        payload = load_legacy_articles(self.project_root)
        if payload:
            await self.repository.seed_articles(payload)

    async def list_articles(self, query: str | None = None, limit: int = 50) -> list[Article]:
        await self._ensure_seeded()
        rows = await self.repository.list_articles(query=query, limit=limit)
        return [Article.model_validate(item) for item in rows]

    async def get_by_slug(self, slug: str) -> Article | None:
        await self._ensure_seeded()
        row = await self.repository.get_article_by_slug(slug)
        if row is None:
            return None
        return Article.model_validate(row)
