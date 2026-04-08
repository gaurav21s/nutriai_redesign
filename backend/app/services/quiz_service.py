"""Service layer for quiz generation and grading."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.exceptions import NotFoundException
from app.repositories.base import CompositeRepository
from app.schemas.quizzes import (
    QuizGenerateRequest,
    QuizHistoryItem,
    QuizQuestion,
    QuizSessionResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from app.services.subscription_service import SubscriptionService
from app.utils.ai_clients import GroqClient
from app.utils.parsers import parse_quiz
from app.utils.prompt_builders import quiz_prompt


class QuizService:
    def __init__(
        self,
        repository: CompositeRepository,
        groq_client: GroqClient,
        subscription_service: SubscriptionService | None = None,
    ) -> None:
        self.repository = repository
        self.groq_client = groq_client
        self.subscription_service = subscription_service

    @staticmethod
    def _parse_iso_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    async def generate(
        self,
        clerk_user_id: str,
        payload: QuizGenerateRequest,
        *,
        session_metadata: dict | None = None,
    ) -> QuizSessionResponse:
        if self.subscription_service is None:
            raise RuntimeError("Subscription service is required for quiz generation")
        await self.subscription_service.consume_nutrition_credits(clerk_user_id, 1, "nutri_quiz")
        raw = await self.groq_client.generate_text(
            quiz_prompt(payload.topic, payload.difficulty, payload.question_count),
            system_prompt="You are a quiz creator specializing in engaging nutrition quizzes.",
            temperature=0.5,
        )

        questions = parse_quiz(raw)
        if len(questions) < payload.question_count:
            # Keep API stable by using whatever valid subset we can parse.
            questions = questions[: payload.question_count]

        session = await self.repository.create_quiz_session(
            clerk_user_id,
            {
                "topic": payload.topic,
                "difficulty": payload.difficulty,
                "questions": questions,
                "raw_response": raw,
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                **(session_metadata or {}),
            },
        )

        return QuizSessionResponse(
            session_id=session["session_id"],
            topic=session["topic"],
            difficulty=session["difficulty"],
            created_at=self._parse_iso_datetime(session["created_at"]),
            questions=[QuizQuestion.model_validate(item) for item in session["questions"]],
            operation_id=session.get("operation_id"),
        )

    async def submit(
        self,
        clerk_user_id: str,
        session_id: str,
        payload: QuizSubmitRequest,
        *,
        attempt_metadata: dict | None = None,
    ) -> QuizSubmitResponse:
        session = await self.repository.get_quiz_session(clerk_user_id, session_id)
        if session is None:
            raise NotFoundException("Quiz session not found")

        questions = session.get("questions", [])
        answer_lookup = {answer.question_index: answer.selected_option.upper() for answer in payload.answers}

        results = []
        correct_answers = 0

        for index, question in enumerate(questions):
            selected = answer_lookup.get(index, "")
            correct = str(question.get("correct_answer", "")).upper()
            is_correct = selected == correct
            if is_correct:
                correct_answers += 1
            results.append(
                {
                    "question_index": index,
                    "is_correct": is_correct,
                    "selected_option": selected,
                    "correct_option": correct,
                    "explanation": question.get("explanation", ""),
                }
            )

        total_questions = len(questions)
        score_percentage = (correct_answers / total_questions * 100.0) if total_questions else 0.0

        submission = {
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "score_percentage": score_percentage,
            "results": results,
        }

        stored = await self.repository.store_quiz_submission(
            clerk_user_id,
            session_id,
            {**submission, **(attempt_metadata or {})},
        )

        return QuizSubmitResponse(
            attempt_id=str(stored.get("attempt_id", "")),
            session_id=session_id,
            total_questions=total_questions,
            correct_answers=correct_answers,
            score_percentage=score_percentage,
            results=results,
            operation_id=stored.get("operation_id"),
        )

    async def get_history(self, clerk_user_id: str, limit: int = 20) -> list[QuizHistoryItem]:
        rows = await self.repository.list_quiz_history(clerk_user_id, limit)
        rows = await self.subscription_service.filter_history_rows(clerk_user_id, rows)
        items = []
        for row in rows:
            items.append(
                QuizHistoryItem(
                    session_id=row["session_id"],
                    topic=row["topic"],
                    difficulty=row["difficulty"],
                    created_at=self._parse_iso_datetime(row["created_at"]),
                    score_percentage=row.get("score_percentage"),
                )
            )
        return items

    async def get_session(self, clerk_user_id: str, session_id: str) -> QuizSessionResponse | None:
        session = await self.repository.get_quiz_session(clerk_user_id, session_id)
        if not await self.subscription_service.can_access_history_row(clerk_user_id, session):
            return None
        return QuizSessionResponse(
            session_id=session["session_id"],
            topic=session["topic"],
            difficulty=session["difficulty"],
            created_at=self._parse_iso_datetime(session["created_at"]),
            questions=[QuizQuestion.model_validate(item) for item in session.get("questions", [])],
            operation_id=session.get("operation_id"),
        )
