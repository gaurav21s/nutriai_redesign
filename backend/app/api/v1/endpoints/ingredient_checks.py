"""Ingredient checker endpoints."""

from fastapi import APIRouter, Depends, Query, Request, UploadFile

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException, NotFoundException
from app.core.security import AuthContext, get_auth_context
from app.dependencies import ai_rate_limit, default_rate_limit, get_ingredient_checks_service
from app.schemas.ingredient_checks import (
    IngredientCheckHistoryResponse,
    IngredientCheckRequest,
    IngredientCheckResponse,
)
from app.services.ingredient_checks_service import IngredientChecksService

router = APIRouter(prefix="/ingredient-checks", tags=["Ingredient Checks"])


@router.post(
    "/analyze",
    response_model=IngredientCheckResponse,
    summary="Analyze ingredients",
    description="Categorize ingredients into healthy/unhealthy and list possible health concerns.",
    dependencies=[Depends(ai_rate_limit)],
)
async def analyze_ingredients(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    settings: Settings = Depends(get_settings),
    service: IngredientChecksService = Depends(get_ingredient_checks_service),
) -> IngredientCheckResponse:
    content_type = request.headers.get("content-type", "")

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        image = form.get("image")
        if not isinstance(image, UploadFile):
            raise AppException("INVALID_REQUEST", "image file is required in multipart payload")
        if image.content_type not in settings.get_allowed_image_types():
            raise AppException("UNSUPPORTED_FILE_TYPE", "Unsupported image type")
        content = await image.read()
        if len(content) > settings.max_upload_size_mb * 1024 * 1024:
            raise AppException("PAYLOAD_TOO_LARGE", "Uploaded image exceeds maximum size", status_code=413)
        return await service.analyze_image(auth.clerk_user_id, content, image.content_type or "image/png")

    try:
        payload = IngredientCheckRequest.model_validate(await request.json())
    except Exception as exc:
        raise AppException("INVALID_REQUEST", "Valid JSON body is required for non-multipart requests") from exc

    if payload.input_mode == "image":
        if not payload.image_base64:
            raise AppException("INVALID_REQUEST", "image_base64 is required for image mode")
        from app.utils.ai_clients import decode_base64_payload

        bytes_payload = decode_base64_payload(payload.image_base64)
        return await service.analyze_image(auth.clerk_user_id, bytes_payload, payload.image_mime_type)

    return await service.analyze_text(auth.clerk_user_id, payload.ingredients_text or "")


@router.get(
    "/history",
    response_model=IngredientCheckHistoryResponse,
    summary="List ingredient analysis history",
    description="Returns historical ingredient check records for the current user.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_ingredient_check_history(
    limit: int = Query(default=20, ge=1, le=100),
    auth: AuthContext = Depends(get_auth_context),
    service: IngredientChecksService = Depends(get_ingredient_checks_service),
) -> IngredientCheckHistoryResponse:
    items = await service.get_history(auth.clerk_user_id, limit)
    return IngredientCheckHistoryResponse(items=items)


@router.get(
    "/history/{record_id}",
    response_model=IngredientCheckResponse,
    summary="Get ingredient analysis record",
    description="Returns one ingredient analysis record by id for the current user.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_ingredient_check_by_id(
    record_id: str,
    auth: AuthContext = Depends(get_auth_context),
    service: IngredientChecksService = Depends(get_ingredient_checks_service),
) -> IngredientCheckResponse:
    record = await service.get_by_id(auth.clerk_user_id, record_id)
    if record is None:
        raise NotFoundException("Ingredient analysis record not found")
    return record
