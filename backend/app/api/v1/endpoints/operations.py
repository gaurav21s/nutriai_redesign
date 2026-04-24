"""Generic operation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from app.core.exceptions import NotFoundException
from app.core.security import AuthContext, get_auth_context
from app.dependencies import default_rate_limit, get_operations_service
from app.schemas.operations import OperationResponse, OperationSubmitRequest
from app.services.operations_service import OperationsService

router = APIRouter(prefix="/operations", tags=["Operations"])


@router.post(
    "",
    response_model=OperationResponse,
    summary="Create operation",
    description="Queues a durable operation for an async-capable workflow.",
    dependencies=[Depends(default_rate_limit)],
)
async def create_operation(
    payload: OperationSubmitRequest,
    background_tasks: BackgroundTasks,
    auth: AuthContext = Depends(get_auth_context),
    service: OperationsService = Depends(get_operations_service),
) -> OperationResponse:
    operation = await service.submit_operation(auth.clerk_user_id, payload)
    if operation.status == "queued":
        background_tasks.add_task(service.run_operation, auth.clerk_user_id, operation.operation_id)
    return OperationResponse(operation=operation)


@router.get(
    "/{operation_id}",
    response_model=OperationResponse,
    summary="Get operation",
    description="Returns durable operation status and result metadata.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_operation(
    operation_id: str,
    auth: AuthContext = Depends(get_auth_context),
    service: OperationsService = Depends(get_operations_service),
) -> OperationResponse:
    return OperationResponse(operation=await service.get_operation(auth.clerk_user_id, operation_id))


@router.get(
    "/{operation_id}/stream",
    summary="Stream operation status",
    description="Streams operation lifecycle updates until the operation completes or fails.",
    dependencies=[Depends(default_rate_limit)],
)
async def stream_operation(
    operation_id: str,
    auth: AuthContext = Depends(get_auth_context),
    service: OperationsService = Depends(get_operations_service),
) -> StreamingResponse:
    return StreamingResponse(
        service.stream_operation(auth.clerk_user_id, operation_id),
        media_type="application/x-ndjson",
    )


@router.get(
    "/{operation_id}/artifact",
    summary="Download operation artifact",
    description="Downloads an exported artifact when the operation produced one.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_operation_artifact(
    operation_id: str,
    auth: AuthContext = Depends(get_auth_context),
    service: OperationsService = Depends(get_operations_service),
) -> StreamingResponse:
    operation = await service.get_operation(auth.clerk_user_id, operation_id)
    artifact = await service.get_artifact_bytes(auth.clerk_user_id, operation_id)
    if artifact is None or not operation.result_ref or operation.result_ref.resource_type != "meal_plan_pdf_export":
        raise NotFoundException("Operation artifact not found")
    return StreamingResponse(iter([artifact]), media_type="application/pdf")
