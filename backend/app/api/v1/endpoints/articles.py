"""Article endpoints."""

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import NotFoundException
from app.core.security import AuthContext, get_auth_context
from app.dependencies import default_rate_limit, get_article_service
from app.schemas.articles import Article, ArticleListResponse
from app.services.article_service import ArticleService

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.get(
    "",
    response_model=ArticleListResponse,
    summary="List articles",
    description="Returns article cards, optionally filtered by query text.",
    dependencies=[Depends(default_rate_limit)],
)
async def list_articles(
    query: str | None = Query(default=None, description="Free-text search by title or summary"),
    limit: int = Query(default=50, ge=1, le=100),
    _auth: AuthContext = Depends(get_auth_context),
    service: ArticleService = Depends(get_article_service),
) -> ArticleListResponse:
    items = await service.list_articles(query=query, limit=limit)
    return ArticleListResponse(items=items)


@router.get(
    "/{slug}",
    response_model=Article,
    summary="Get article details",
    description="Returns full article content by slug.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_article_by_slug(
    slug: str,
    _auth: AuthContext = Depends(get_auth_context),
    service: ArticleService = Depends(get_article_service),
) -> Article:
    article = await service.get_by_slug(slug)
    if article is None:
        raise NotFoundException("Article not found")
    return article
