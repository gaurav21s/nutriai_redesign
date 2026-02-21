"""Article schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Article(BaseModel):
    id: str
    slug: str
    title: str
    summary: str
    content: str
    created_at: datetime


class ArticleListResponse(BaseModel):
    items: list[Article]
