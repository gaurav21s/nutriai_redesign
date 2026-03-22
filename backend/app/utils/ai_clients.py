"""Provider adapters for Groq, Together, and Gemini."""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
from typing import Sequence

from app.core.exceptions import ConfigurationException, ExternalServiceException


@dataclass(slots=True)
class Message:
    role: str
    content: str


def _response_text(response: object) -> str:
    content = getattr(response, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(part.strip() for part in parts if part.strip()).strip()
    return str(content).strip()


class GeminiClient:
    """Gemini adapter for text and image prompts."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        if not api_key:
            raise ConfigurationException("GOOGLE_API_KEY is required for Gemini features")
        self.api_key = api_key
        self.model_name = model_name

    async def generate_text(self, prompt: str) -> str:
        return await asyncio.to_thread(self._generate_text_sync, prompt)

    def _generate_text_sync(self, prompt: str) -> str:
        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(model=self.model_name, contents=prompt)
            return str(getattr(response, "text", "") or "").strip()
        except Exception as exc:
            raise ExternalServiceException("Gemini text generation failed", details={"reason": str(exc)}) from exc

    async def generate_with_image(self, prompt: str, image_bytes: bytes, mime_type: str = "image/png") -> str:
        return await asyncio.to_thread(self._generate_with_image_sync, prompt, image_bytes, mime_type)

    def _generate_with_image_sync(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)],
            )
            return str(getattr(response, "text", "") or "").strip()
        except Exception as exc:
            raise ExternalServiceException("Gemini image generation failed", details={"reason": str(exc)}) from exc

    async def identify_ingredients_from_image(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        prompt = "Identify ingredients in this image and return only a comma-separated list."
        return await self.generate_with_image(prompt, image_bytes, mime_type)


class TogetherClient:
    """Together adapter for text generation."""

    def __init__(self, api_key: str, model_name: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo") -> None:
        if not api_key:
            raise ConfigurationException("TOGETHER_API_KEY is required for Together features")
        self.api_key = api_key
        self.model_name = model_name
        self.fallback_model_name = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

    async def generate_text(self, prompt: str, temperature: float = 0.2) -> str:
        return await asyncio.to_thread(self._generate_text_sync, prompt, temperature)

    def _generate_text_sync(self, prompt: str, temperature: float) -> str:
        from langchain_together import ChatTogether

        models_to_try = [self.model_name]
        if self.fallback_model_name not in models_to_try:
            models_to_try.append(self.fallback_model_name)

        last_error: Exception | None = None
        access_blocked = False
        for candidate in models_to_try:
            try:
                model = ChatTogether(
                    api_key=self.api_key,
                    model=candidate,
                    temperature=temperature,
                )
                response = model.invoke([("human", prompt)])
                return _response_text(response)
            except Exception as exc:
                last_error = exc
                reason = str(exc).lower()
                if "unable to access non-serverless model" in reason:
                    access_blocked = True
                    continue
                if "non-serverless model" not in reason:
                    break

        if access_blocked:
            from app.utils.fallback_ai_clients import FallbackTogetherClient

            # Keep meal-plan and chat available in development when provider access is restricted.
            return asyncio.run(FallbackTogetherClient().generate_text(prompt, temperature))

        raise ExternalServiceException(
            "Together generation failed",
            details={"reason": str(last_error) if last_error else "unknown error"},
        ) from last_error


class GroqClient:
    """Groq adapter for text/chat generation."""

    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile") -> None:
        if not api_key:
            raise ConfigurationException("GROQ_API_KEY is required for Groq features")
        self.api_key = api_key
        self.model_name = model_name

    async def generate_text(self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2) -> str:
        return await asyncio.to_thread(self._generate_text_sync, prompt, system_prompt, temperature)

    def _generate_text_sync(self, prompt: str, system_prompt: str | None, temperature: float) -> str:
        try:
            from langchain_groq import ChatGroq

            model = ChatGroq(
                api_key=self.api_key,
                model=self.model_name,
                temperature=temperature,
            )

            messages: list[tuple[str, str]] = []
            if system_prompt:
                messages.append(("system", system_prompt))
            messages.append(("human", prompt))

            response = model.invoke(messages)
            return _response_text(response)
        except Exception as exc:
            raise ExternalServiceException("Groq generation failed", details={"reason": str(exc)}) from exc


def decode_base64_payload(payload: str) -> bytes:
    """Decode a base64 payload that may include a data URL prefix."""
    cleaned = payload
    if "," in payload and payload.startswith("data:"):
        cleaned = payload.split(",", 1)[1]
    return base64.b64decode(cleaned)


def normalize_chat_messages(messages: Sequence[dict]) -> list[Message]:
    normalized: list[Message] = []
    for item in messages:
        role = str(item.get("role", "user"))
        content = str(item.get("content", ""))
        if content:
            normalized.append(Message(role=role, content=content))
    return normalized
