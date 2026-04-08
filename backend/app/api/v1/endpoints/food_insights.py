"""Food insight endpoints."""

from fastapi import APIRouter, Depends, Query, Request, UploadFile

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException, NotFoundException
from app.core.security import AuthContext, get_auth_context
from app.dependencies import ai_rate_limit, default_rate_limit, get_food_insights_service, get_operations_service
from app.schemas.food_insights import (
    FoodInsightAnalyzeRequest,
    FoodInsightHistoryResponse,
    FoodInsightResponse,
)
from app.schemas.operations import OperationSubmitRequest
from app.services.food_insights_service import FoodInsightsService

router = APIRouter(prefix="/food-insights", tags=["Food Insights"])


@router.post(
    "/analyze",
    response_model=FoodInsightResponse,
    summary="Analyze food nutrition",
    description="Analyze nutrition from text input or uploaded food image.",
    dependencies=[Depends(ai_rate_limit)],
)
async def analyze_food(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    settings: Settings = Depends(get_settings),
    service: FoodInsightsService = Depends(get_food_insights_service),
    operations_service=Depends(get_operations_service),
) -> FoodInsightResponse:
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
        operation = await operations_service.submit_and_wait(
            auth.clerk_user_id,
            OperationSubmitRequest(
                feature="food_insight_analyze",
                payload={"input_mode": "image", "image_mime_type": image.content_type or "image/png"},
            ),
            runtime_payload={"image_bytes": content},
        )
        return FoodInsightResponse.model_validate(operation.response_payload)

    try:
        payload = FoodInsightAnalyzeRequest.model_validate(await request.json())
    except Exception as exc:
        raise AppException("INVALID_REQUEST", "Valid JSON body is required for non-multipart requests") from exc

    if payload.input_mode == "image":
        if not payload.image_base64:
            raise AppException("INVALID_REQUEST", "image_base64 is required for image mode")
        from app.utils.ai_clients import decode_base64_payload

        image_bytes = decode_base64_payload(payload.image_base64)
        operation = await operations_service.submit_and_wait(
            auth.clerk_user_id,
            OperationSubmitRequest(
                feature="food_insight_analyze",
                payload=payload.model_dump(mode="json"),
            ),
            runtime_payload={"image_bytes": image_bytes},
        )
        return FoodInsightResponse.model_validate(operation.response_payload)

    operation = await operations_service.submit_and_wait(
        auth.clerk_user_id,
        OperationSubmitRequest(feature="food_insight_analyze", payload=payload.model_dump(mode="json")),
    )
    return FoodInsightResponse.model_validate(operation.response_payload)


@router.get(
    "/history",
    response_model=FoodInsightHistoryResponse,
    summary="List food insight history",
    description="Returns recent food insight analysis records for the current user.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_food_insight_history(
    limit: int = Query(default=20, ge=1, le=100),
    auth: AuthContext = Depends(get_auth_context),
    service: FoodInsightsService = Depends(get_food_insights_service),
) -> FoodInsightHistoryResponse:
    items = await service.get_history(auth.clerk_user_id, limit)
    return FoodInsightHistoryResponse(items=items)


@router.get(
    "/history/{record_id}",
    response_model=FoodInsightResponse,
    summary="Get a food insight record",
    description="Returns one food insight analysis record by id for the current user.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_food_insight_by_id(
    record_id: str,
    auth: AuthContext = Depends(get_auth_context),
    service: FoodInsightsService = Depends(get_food_insights_service),
) -> FoodInsightResponse:
    record = await service.get_by_id(auth.clerk_user_id, record_id)
    if record is None:
        raise NotFoundException("Food insight record not found")
    return record
