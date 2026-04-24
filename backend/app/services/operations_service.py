"""Shared operation orchestration for async-capable workflows."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.config import Settings
from app.core.coordination import SharedCoordinator
from app.core.exceptions import AppException, NotFoundException
from app.repositories.base import CompositeRepository
from app.schemas.calculators import BMIRequest, CaloriesRequest
from app.schemas.food_insights import FoodInsightAnalyzeRequest, FoodInsightResponse
from app.schemas.ingredient_checks import IngredientCheckRequest, IngredientCheckResponse
from app.schemas.meal_plans import MealPlanGenerateRequest, MealPlanPdfRequest, MealPlanResponse
from app.schemas.nutri_chat import ChatMessage
from app.schemas.operations import OperationRecord, OperationResultRef, OperationSubmitRequest
from app.schemas.quizzes import QuizGenerateRequest, QuizSessionResponse, QuizSubmitRequest, QuizSubmitResponse
from app.schemas.recipes import RecipeGenerateRequest, RecipeResponse
from app.schemas.smart_picks import SmartPickGenerateRequest, SmartPickResponse
from app.services.calculator_service import CalculatorService
from app.services.food_insights_service import FoodInsightsService
from app.services.ingredient_checks_service import IngredientChecksService
from app.services.meal_plan_service import MealPlanService
from app.services.nutri_chat_service import NutriChatService
from app.services.quiz_service import QuizService
from app.services.recipe_service import RecipeService
from app.services.smart_picks_service import SmartPicksService
from app.services.subscription_service import SubscriptionService
from app.utils.ai_clients import decode_base64_payload


class OperationsService:
    def __init__(
        self,
        repository: CompositeRepository,
        settings: Settings,
        coordinator: SharedCoordinator,
        subscription_service: SubscriptionService,
        calculator_service: CalculatorService,
        recipe_service: RecipeService,
        smart_picks_service: SmartPicksService,
        food_insights_service: FoodInsightsService | None,
        ingredient_checks_service: IngredientChecksService | None,
        meal_plan_service: MealPlanService | None,
        quiz_service: QuizService,
        nutri_chat_service: NutriChatService,
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.coordinator = coordinator
        self.subscription_service = subscription_service
        self.calculator_service = calculator_service
        self.recipe_service = recipe_service
        self.smart_picks_service = smart_picks_service
        self.food_insights_service = food_insights_service
        self.ingredient_checks_service = ingredient_checks_service
        self.meal_plan_service = meal_plan_service
        self.quiz_service = quiz_service
        self.nutri_chat_service = nutri_chat_service
        self._background_tasks: set[asyncio.Task[Any]] = set()

    @staticmethod
    def _workload_pool(feature: str, payload: dict[str, Any]) -> str:
        if feature == "chat_turn":
            return "chat_agent"
        if feature == "meal_plan_export_pdf":
            return "export_background"
        if feature in {"food_insight_analyze", "ingredient_check_analyze"} and payload.get("input_mode") == "image":
            return "vision_image_analysis"
        return "text_generation"

    @staticmethod
    def _resource_key(feature: str, resource_scope: dict[str, str]) -> str | None:
        if feature == "chat_turn" and resource_scope.get("session_id"):
            return f"chat-session:{resource_scope['session_id']}"
        if feature == "meal_plan_export_pdf" and resource_scope.get("record_id"):
            return f"meal-plan-export:{resource_scope['record_id']}"
        if feature == "quiz_submit" and resource_scope.get("session_id"):
            return f"quiz-submit:{resource_scope['session_id']}"
        return None

    @staticmethod
    def _timeout_seconds(feature: str, payload: dict[str, Any]) -> int:
        if feature == "chat_turn":
            return 60
        if feature == "meal_plan_export_pdf":
            return 180
        if feature in {"food_insight_analyze", "ingredient_check_analyze"} and payload.get("input_mode") == "image":
            return 120
        return 90

    async def submit_operation(
        self,
        clerk_user_id: str,
        payload: OperationSubmitRequest,
        *,
        request_id: str | None = None,
    ) -> OperationRecord:
        if payload.idempotency_key:
            existing = await self.repository.get_operation_by_idempotency(
                clerk_user_id,
                payload.feature,
                payload.idempotency_key,
            )
            if existing:
                return OperationRecord.model_validate(existing)

        tier = (await self.subscription_service.get_current_subscription(clerk_user_id)).subscription.tier
        workload_pool = self._workload_pool(payload.feature, payload.payload)
        await self.coordinator.register_queue(clerk_user_id, tier, workload_pool)

        sequence_no: int | None = None
        if payload.feature == "chat_turn":
            session_id = str(payload.resource_scope.get("session_id") or payload.payload.get("session_id") or "").strip()
            if not session_id:
                raise AppException("INVALID_OPERATION", "Chat operations require a session_id")
            try:
                sequence_no = await self.repository.reserve_chat_sequence(clerk_user_id, session_id)
            except ValueError as exc:
                raise NotFoundException("Chat session not found") from exc

        operation = await self.repository.create_operation(
            clerk_user_id,
            {
                "operation_id": str(uuid4()),
                "feature": payload.feature,
                "status": "queued",
                "queue_tier": tier,
                "resource_scope": payload.resource_scope,
                "workload_pool": workload_pool,
                "idempotency_key": payload.idempotency_key,
                "request_payload": payload.payload,
                "response_payload": {},
                "sequence_no": sequence_no,
                "request_id": request_id,
            },
        )
        return OperationRecord.model_validate(operation)

    async def get_operation(self, clerk_user_id: str, operation_id: str) -> OperationRecord:
        operation = await self.repository.get_operation(clerk_user_id, operation_id)
        if operation is None:
            raise NotFoundException("Operation not found")
        return OperationRecord.model_validate(operation)

    def schedule_operation(self, clerk_user_id: str, operation_id: str) -> None:
        task = asyncio.create_task(self.run_operation(clerk_user_id, operation_id))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def wait_for_operation(self, clerk_user_id: str, operation_id: str, timeout_seconds: int | None = None) -> OperationRecord:
        deadline = asyncio.get_running_loop().time() + float(timeout_seconds or self.settings.request_timeout_seconds)
        while True:
            operation = await self.get_operation(clerk_user_id, operation_id)
            if operation.status in {"completed", "failed", "cancelled", "expired"}:
                return operation
            if asyncio.get_running_loop().time() >= deadline:
                raise AppException("OPERATION_TIMEOUT", "Operation did not complete in time", status_code=504)
            await asyncio.sleep(self.settings.operations_stream_poll_seconds)

    async def submit_and_wait(
        self,
        clerk_user_id: str,
        payload: OperationSubmitRequest,
        *,
        request_id: str | None = None,
        runtime_payload: dict[str, Any] | None = None,
    ) -> OperationRecord:
        operation = await self.submit_operation(clerk_user_id, payload, request_id=request_id)
        if operation.status == "completed":
            return operation
        operation = await self.run_operation(clerk_user_id, operation.operation_id, runtime_payload=runtime_payload)
        if operation.status not in {"completed", "failed", "cancelled", "expired"}:
            operation = await self.wait_for_operation(clerk_user_id, operation.operation_id)
        return operation

    async def run_operation(
        self,
        clerk_user_id: str,
        operation_id: str,
        *,
        runtime_payload: dict[str, Any] | None = None,
    ) -> OperationRecord:
        operation = await self.get_operation(clerk_user_id, operation_id)
        if operation.status == "completed":
            return operation
        if operation.status == "running":
            return operation

        await self.coordinator.mark_dequeued(clerk_user_id, operation.workload_pool)

        resource_key = self._resource_key(operation.feature, operation.resource_scope)
        timeout_seconds = self._timeout_seconds(operation.feature, operation.request_payload)
        async with self.coordinator.execution_slot(
            clerk_user_id,
            operation.queue_tier,
            operation.workload_pool,
            resource_key=resource_key,
            timeout_seconds=timeout_seconds,
        ):
            await self.repository.update_operation(
                clerk_user_id,
                operation_id,
                {"status": "running", "started_at": self._now_iso()},
            )
            try:
                response_payload, result_ref = await asyncio.wait_for(
                    self._execute_operation(clerk_user_id, operation, runtime_payload=runtime_payload),
                    timeout=timeout_seconds,
                )
            except Exception as exc:
                updated = await self.repository.update_operation(
                    clerk_user_id,
                    operation_id,
                    {
                        "status": "failed",
                        "error_code": getattr(exc, "code", "OPERATION_FAILED"),
                        "error_message": str(exc),
                        "finished_at": self._now_iso(),
                    },
                )
                if updated is None:
                    raise NotFoundException("Operation not found")
                if isinstance(exc, AppException):
                    raise
                raise AppException("OPERATION_FAILED", str(exc), status_code=500) from exc

            updated = await self.repository.update_operation(
                clerk_user_id,
                operation_id,
                {
                    "status": "completed",
                    "response_payload": response_payload,
                    "result_ref": result_ref.model_dump(mode="json"),
                    "finished_at": self._now_iso(),
                },
            )
            if updated is None:
                raise NotFoundException("Operation not found")
            return OperationRecord.model_validate(updated)

    async def stream_operation(self, clerk_user_id: str, operation_id: str) -> AsyncIterator[str]:
        last_status = ""
        while True:
            operation = await self.get_operation(clerk_user_id, operation_id)
            event_type = operation.status if operation.status in {"queued", "running", "completed", "failed"} else "heartbeat"
            if operation.status != last_status or event_type == "heartbeat":
                payload = {"type": event_type, "operation": operation.model_dump(mode="json")}
                yield f"{json.dumps(payload, ensure_ascii=True)}\n"
                last_status = operation.status
            if operation.status in {"completed", "failed", "cancelled", "expired"}:
                break
            await asyncio.sleep(self.settings.operations_stream_poll_seconds)

    async def get_artifact_bytes(self, clerk_user_id: str, operation_id: str) -> bytes | None:
        operation = await self.get_operation(clerk_user_id, operation_id)
        if not operation.result_ref:
            return None
        if operation.result_ref.resource_type == "meal_plan_pdf_export":
            if self.meal_plan_service is None:
                return None
            return await self.meal_plan_service.get_pdf_export_bytes(clerk_user_id, operation.result_ref.resource_id)
        return None

    async def _execute_operation(
        self,
        clerk_user_id: str,
        operation: OperationRecord,
        *,
        runtime_payload: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], OperationResultRef]:
        payload = {**operation.request_payload, **(runtime_payload or {})}
        operation_metadata = {
            "operation_id": operation.operation_id,
            "sequence_no": operation.sequence_no,
        }

        if operation.feature == "chat_turn":
            session_id = str(operation.resource_scope.get("session_id") or payload.get("session_id") or "").strip()
            content = str(payload.get("content") or "").strip()
            result = await self.nutri_chat_service.send_message_with_operation(
                clerk_user_id,
                session_id,
                content,
                operation_id=operation.operation_id,
                sequence_no=operation.sequence_no,
            )
            return result.model_dump(mode="json"), OperationResultRef(
                resource_type="chat_message",
                resource_id=result.id,
                session_id=session_id,
                metadata={"sequence_no": operation.sequence_no},
            )

        if operation.feature == "meal_plan_generate":
            if self.meal_plan_service is None:
                raise AppException("MISCONFIGURATION", "Meal plan generation is not configured", status_code=500)
            result = await self.meal_plan_service.generate(
                clerk_user_id,
                MealPlanGenerateRequest.model_validate(payload),
                record_metadata={"operation_id": operation.operation_id},
            )
            return result.model_dump(mode="json"), OperationResultRef(resource_type="meal_plan", resource_id=result.id)

        if operation.feature == "recipe_generate":
            result = await self.recipe_service.generate(
                clerk_user_id,
                RecipeGenerateRequest.model_validate(payload),
                record_metadata={"operation_id": operation.operation_id},
            )
            return result.model_dump(mode="json"), OperationResultRef(resource_type="recipe", resource_id=result.id)

        if operation.feature == "recommendation_generate":
            result = await self.smart_picks_service.generate(
                clerk_user_id,
                SmartPickGenerateRequest.model_validate(payload),
                record_metadata={"operation_id": operation.operation_id},
            )
            return result.model_dump(mode="json"), OperationResultRef(resource_type="recommendation", resource_id=result.id)

        if operation.feature == "food_insight_analyze":
            if self.food_insights_service is None:
                raise AppException("MISCONFIGURATION", "Food insights are not configured", status_code=500)
            request = FoodInsightAnalyzeRequest.model_validate(payload)
            if request.input_mode == "image":
                image_bytes = payload.get("image_bytes")
                if not isinstance(image_bytes, bytes):
                    if request.image_base64:
                        image_bytes = decode_base64_payload(request.image_base64)
                    else:
                        raise AppException("INVALID_OPERATION", "Image operations require image_bytes")
                result = await self.food_insights_service.analyze_image(
                    clerk_user_id,
                    image_bytes,
                    request.image_mime_type,
                    record_metadata={"operation_id": operation.operation_id},
                )
            else:
                result = await self.food_insights_service.analyze_text(
                    clerk_user_id,
                    request.text or "",
                    record_metadata={"operation_id": operation.operation_id},
                )
            return result.model_dump(mode="json"), OperationResultRef(resource_type="food_insight", resource_id=result.id)

        if operation.feature == "ingredient_check_analyze":
            if self.ingredient_checks_service is None:
                raise AppException("MISCONFIGURATION", "Ingredient checks are not configured", status_code=500)
            request = IngredientCheckRequest.model_validate(payload)
            if request.input_mode == "image":
                image_bytes = payload.get("image_bytes")
                if not isinstance(image_bytes, bytes):
                    if request.image_base64:
                        image_bytes = decode_base64_payload(request.image_base64)
                    else:
                        raise AppException("INVALID_OPERATION", "Image operations require image_bytes")
                result = await self.ingredient_checks_service.analyze_image(
                    clerk_user_id,
                    image_bytes,
                    request.image_mime_type,
                    record_metadata={"operation_id": operation.operation_id},
                )
            else:
                result = await self.ingredient_checks_service.analyze_text(
                    clerk_user_id,
                    request.ingredients_text or "",
                    record_metadata={"operation_id": operation.operation_id},
                )
            return result.model_dump(mode="json"), OperationResultRef(
                resource_type="ingredient_check",
                resource_id=result.id,
            )

        if operation.feature == "quiz_generate":
            result = await self.quiz_service.generate(
                clerk_user_id,
                QuizGenerateRequest.model_validate(payload),
                session_metadata={"operation_id": operation.operation_id},
            )
            return result.model_dump(mode="json"), OperationResultRef(
                resource_type="quiz_session",
                resource_id=result.session_id,
                session_id=result.session_id,
            )

        if operation.feature == "quiz_submit":
            session_id = str(operation.resource_scope.get("session_id") or payload.get("session_id") or "").strip()
            result = await self.quiz_service.submit(
                clerk_user_id,
                session_id,
                QuizSubmitRequest.model_validate(payload),
                attempt_metadata={"operation_id": operation.operation_id},
            )
            return result.model_dump(mode="json"), OperationResultRef(
                resource_type="quiz_attempt",
                resource_id=result.attempt_id,
                session_id=session_id,
            )

        if operation.feature == "meal_plan_export_pdf":
            if self.meal_plan_service is None:
                raise AppException("MISCONFIGURATION", "Meal plan export is not configured", status_code=500)
            record_id = str(operation.resource_scope.get("record_id") or payload.get("record_id") or "").strip()
            request = MealPlanPdfRequest.model_validate(payload)
            export = await self.meal_plan_service.create_pdf_export(
                clerk_user_id,
                record_id,
                request.full_name,
                request.age,
                operation_id=operation.operation_id,
                consume_export_quota=True,
            )
            return (
                export.model_dump(mode="json"),
                OperationResultRef(
                    resource_type="meal_plan_pdf_export",
                    resource_id=export.id,
                    metadata={"record_id": record_id, "byte_size": export.byte_size},
                ),
            )

        raise AppException("UNSUPPORTED_OPERATION", f"Unsupported operation feature: {operation.feature}")

    async def calculate_bmi_with_operation(self, clerk_user_id: str, payload: BMIRequest) -> dict[str, Any]:
        response = await self.calculator_service.preview_bmi(payload)
        await self.calculator_service.save_bmi_preview(
            clerk_user_id,
            payload,
            response,
            record_metadata={"idempotency_key": payload.idempotency_key} if payload.idempotency_key else None,
        )
        return response.model_dump(mode="json")

    async def calculate_calories_with_operation(self, clerk_user_id: str, payload: CaloriesRequest) -> dict[str, Any]:
        response = await self.calculator_service.preview_calories(payload)
        await self.calculator_service.save_calories_preview(
            clerk_user_id,
            payload,
            response,
            record_metadata={"idempotency_key": payload.idempotency_key} if payload.idempotency_key else None,
        )
        return response.model_dump(mode="json")

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(tz=timezone.utc).isoformat()
