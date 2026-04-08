"""Quiz schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


QuizDifficulty = Literal["easy", "medium", "hard"]


class QuizGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    difficulty: QuizDifficulty
    question_count: int = Field(default=5, ge=3, le=10)


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_answer: str
    explanation: str


class QuizSessionResponse(BaseModel):
    session_id: str
    topic: str
    difficulty: QuizDifficulty
    created_at: datetime
    questions: list[QuizQuestion]
    operation_id: str | None = None


class QuizAnswer(BaseModel):
    question_index: int = Field(..., ge=0)
    selected_option: str = Field(..., min_length=1, max_length=1)


class QuizSubmitRequest(BaseModel):
    answers: list[QuizAnswer]
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class QuizAnswerResult(BaseModel):
    question_index: int
    is_correct: bool
    selected_option: str
    correct_option: str
    explanation: str


class QuizSubmitResponse(BaseModel):
    attempt_id: str
    session_id: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    results: list[QuizAnswerResult]
    operation_id: str | None = None


class QuizHistoryItem(BaseModel):
    session_id: str
    topic: str
    difficulty: QuizDifficulty
    created_at: datetime
    score_percentage: float | None = None


class QuizHistoryResponse(BaseModel):
    items: list[QuizHistoryItem]
