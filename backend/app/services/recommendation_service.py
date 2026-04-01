"""Service layer for recommendations feature."""

from __future__ import annotations

from app.repositories.base import CompositeRepository
from app.schemas.recommendations import RecommendationGenerateRequest, RecommendationResponse
from app.utils.ai_clients import GroqClient
from app.utils.parsers import parse_bullet_recommendations
from app.utils.prompt_builders import recommendation_prompt


class RecommendationService:
    def __init__(self, repository: CompositeRepository, groq_client: GroqClient) -> None:
        self.repository = repository
        self.groq_client = groq_client

    async def preview(self, payload: RecommendationGenerateRequest) -> RecommendationResponse:
        raw = await self.groq_client.generate_text(
            recommendation_prompt(payload.query, payload.recommendation_type),
            system_prompt="You are a nutrition recommendation assistant.",
            temperature=0.3,
        )
        recommendations = parse_bullet_recommendations(raw)

        return RecommendationResponse.model_validate(
            {
                "id": "preview",
                "created_at": "1970-01-01T00:00:00+00:00",
                "title": f"Recommendations for {payload.query}",
                "recommendations": recommendations,
                "raw_response": raw,
            }
        )

    async def save_preview(self, clerk_user_id: str, payload: RecommendationGenerateRequest, response: RecommendationResponse) -> dict:
        return await self.repository.create_record(
            "recommendations",
            clerk_user_id,
            {
                "title": response.title,
                "recommendations": response.recommendations,
                "raw_response": response.raw_response,
                "input": payload.model_dump(),
            },
        )

    async def generate(self, clerk_user_id: str, payload: RecommendationGenerateRequest) -> RecommendationResponse:
        preview = await self.preview(payload)
        record = await self.save_preview(clerk_user_id, payload, preview)
        return RecommendationResponse.model_validate(record)

    async def get_history(self, clerk_user_id: str, limit: int = 20) -> list[RecommendationResponse]:
        rows = await self.repository.list_records("recommendations", clerk_user_id, limit)
        return [RecommendationResponse.model_validate(item) for item in rows]
