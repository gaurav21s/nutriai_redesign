"""Health and readiness endpoints."""

from fastapi import APIRouter, Depends

from app.dependencies import default_rate_limit

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    summary="Service health check",
    description="Returns API health status and version metadata.",
    dependencies=[Depends(default_rate_limit)],
)
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "nutriai-api", "version": "v1"}
