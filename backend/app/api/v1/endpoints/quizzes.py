"""Quiz endpoints."""

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import NotFoundException
from app.core.security import AuthContext, get_auth_context
from app.dependencies import ai_rate_limit, default_rate_limit, get_quiz_service
from app.schemas.quizzes import (
    QuizGenerateRequest,
    QuizHistoryResponse,
    QuizSessionResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post(
    "/generate",
    response_model=QuizSessionResponse,
    summary="Generate quiz",
    description="Generates a quiz session based on topic and difficulty.",
    dependencies=[Depends(ai_rate_limit)],
)
async def generate_quiz(
    payload: QuizGenerateRequest,
    auth: AuthContext = Depends(get_auth_context),
    service: QuizService = Depends(get_quiz_service),
) -> QuizSessionResponse:
    return await service.generate(auth.clerk_user_id, payload)


@router.post(
    "/{session_id}/submit",
    response_model=QuizSubmitResponse,
    summary="Submit quiz answers",
    description="Evaluates a submitted quiz attempt and returns score with explanations.",
    dependencies=[Depends(default_rate_limit)],
)
async def submit_quiz(
    session_id: str,
    payload: QuizSubmitRequest,
    auth: AuthContext = Depends(get_auth_context),
    service: QuizService = Depends(get_quiz_service),
) -> QuizSubmitResponse:
    return await service.submit(auth.clerk_user_id, session_id, payload)


@router.get(
    "/history",
    response_model=QuizHistoryResponse,
    summary="List quiz history",
    description="Returns historical quiz sessions and latest score metadata.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_quiz_history(
    limit: int = Query(default=20, ge=1, le=100),
    auth: AuthContext = Depends(get_auth_context),
    service: QuizService = Depends(get_quiz_service),
) -> QuizHistoryResponse:
    items = await service.get_history(auth.clerk_user_id, limit)
    return QuizHistoryResponse(items=items)


@router.get(
    "/history/{session_id}",
    response_model=QuizSessionResponse,
    summary="Get quiz session",
    description="Returns generated quiz questions for an existing session.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_quiz_session(
    session_id: str,
    auth: AuthContext = Depends(get_auth_context),
    service: QuizService = Depends(get_quiz_service),
) -> QuizSessionResponse:
    session = await service.get_session(auth.clerk_user_id, session_id)
    if session is None:
        raise NotFoundException("Quiz session not found")
    return session
