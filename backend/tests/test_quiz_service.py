import asyncio

from app.repositories.in_memory import InMemoryRepository
from app.schemas.quizzes import QuizAnswer, QuizSubmitRequest
from app.services.quiz_service import QuizService


class DummyGroq:
    async def generate_text(self, *args, **kwargs):
        return ""


def test_quiz_submit_scores_correctly():
    async def run_test() -> None:
        repository = InMemoryRepository()
        service = QuizService(repository=repository, groq_client=DummyGroq())

        session = await repository.create_quiz_session(
            "user-1",
            {
                "topic": "nutrition",
                "difficulty": "easy",
                "questions": [
                    {
                        "question": "Q1",
                        "options": ["A1", "B1"],
                        "correct_answer": "A",
                        "explanation": "Because",
                    },
                    {
                        "question": "Q2",
                        "options": ["A2", "B2"],
                        "correct_answer": "B",
                        "explanation": "Because",
                    },
                ],
                "created_at": "2025-01-01T00:00:00+00:00",
            },
        )

        result = await service.submit(
            clerk_user_id="user-1",
            session_id=session["session_id"],
            payload=QuizSubmitRequest(
                answers=[
                    QuizAnswer(question_index=0, selected_option="A"),
                    QuizAnswer(question_index=1, selected_option="A"),
                ]
            ),
        )

        assert result.total_questions == 2
        assert result.correct_answers == 1
        assert result.score_percentage == 50.0

    asyncio.run(run_test())
