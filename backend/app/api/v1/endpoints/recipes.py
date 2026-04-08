"""Recipe and shopping-link endpoints."""

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import NotFoundException
from app.core.security import AuthContext, get_auth_context
from app.dependencies import ai_rate_limit, default_rate_limit, get_operations_service, get_recipe_service
from app.schemas.operations import OperationSubmitRequest
from app.schemas.recipes import (
    RecipeGenerateRequest,
    RecipeHistoryResponse,
    RecipeResponse,
    ShoppingLinksRequest,
    ShoppingLinksResponse,
)
from app.services.recipe_service import RecipeService

router = APIRouter(prefix="/recipes", tags=["Recipes"])


@router.post(
    "/generate",
    response_model=RecipeResponse,
    summary="Generate recipe",
    description="Generates a normal, healthier, or new healthy recipe.",
    dependencies=[Depends(ai_rate_limit)],
)
async def generate_recipe(
    payload: RecipeGenerateRequest,
    auth: AuthContext = Depends(get_auth_context),
    service: RecipeService = Depends(get_recipe_service),
    operations_service=Depends(get_operations_service),
) -> RecipeResponse:
    operation = await operations_service.submit_and_wait(
        auth.clerk_user_id,
        OperationSubmitRequest(
            feature="recipe_generate",
            payload=payload.model_dump(mode="json"),
            idempotency_key=getattr(payload, "idempotency_key", None),
        ),
    )
    return RecipeResponse.model_validate(operation.response_payload)


@router.post(
    "/shopping-links",
    response_model=ShoppingLinksResponse,
    summary="Generate shopping links",
    description="Builds Amazon and Blinkit shopping links for ingredient list.",
    dependencies=[Depends(default_rate_limit)],
)
async def generate_shopping_links(
    payload: ShoppingLinksRequest,
    _auth: AuthContext = Depends(get_auth_context),
    service: RecipeService = Depends(get_recipe_service),
) -> ShoppingLinksResponse:
    links = await service.get_shopping_links(payload.ingredients)
    return ShoppingLinksResponse(links=links)


@router.get(
    "/history",
    response_model=RecipeHistoryResponse,
    summary="List recipe history",
    description="Returns generated recipes for the current user.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_recipe_history(
    limit: int = Query(default=20, ge=1, le=100),
    auth: AuthContext = Depends(get_auth_context),
    service: RecipeService = Depends(get_recipe_service),
) -> RecipeHistoryResponse:
    items = await service.get_history(auth.clerk_user_id, limit)
    return RecipeHistoryResponse(items=items)


@router.get(
    "/history/{record_id}",
    response_model=RecipeResponse,
    summary="Get recipe record",
    description="Returns one recipe generation record by id.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_recipe_by_id(
    record_id: str,
    auth: AuthContext = Depends(get_auth_context),
    service: RecipeService = Depends(get_recipe_service),
) -> RecipeResponse:
    record = await service.get_by_id(auth.clerk_user_id, record_id)
    if record is None:
        raise NotFoundException("Recipe record not found")
    return record
