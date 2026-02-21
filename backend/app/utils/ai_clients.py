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


class GeminiClient:
    """Gemini adapter for text and image prompts."""

    def __init__(self, api_key: str, model_name: str = "gemini-3-flash-preview") -> None:
        if not api_key:
            raise ConfigurationException("GOOGLE_API_KEY is required for Gemini features")
        self.api_key = api_key
        self.model_name = model_name

    async def generate_text(self, prompt: str) -> str:
        return await asyncio.to_thread(self._generate_text_sync, prompt)

    def _generate_text_sync(self, prompt: str) -> str:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            return (response.text or "").strip()
        except Exception as exc:
            raise ExternalServiceException("Gemini text generation failed", details={"reason": str(exc)}) from exc

    async def generate_with_image(self, prompt: str, image_bytes: bytes, mime_type: str = "image/png") -> str:
        return await asyncio.to_thread(self._generate_with_image_sync, prompt, image_bytes, mime_type)

    def _generate_with_image_sync(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                [
                    prompt,
                    {
                        "mime_type": mime_type,
                        "data": image_bytes,
                    },
                ]
            )
            return (response.text or "").strip()
        except Exception as exc:
            raise ExternalServiceException("Gemini image generation failed", details={"reason": str(exc)}) from exc

    async def identify_ingredients_from_image(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        prompt = "Identify ingredients in this image and return only a comma-separated list."
        return await self.generate_with_image(prompt, image_bytes, mime_type)


class TogetherClient:
    """Together adapter for text generation."""

    def __init__(self, api_key: str, model_name: str = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo") -> None:
        if not api_key:
            raise ConfigurationException("TOGETHER_API_KEY is required for Together features")
        self.api_key = api_key
        self.model_name = model_name

    async def generate_text(self, prompt: str, temperature: float = 0.2) -> str:
        return await asyncio.to_thread(self._generate_text_sync, prompt, temperature)

    def _generate_text_sync(self, prompt: str, temperature: float) -> str:
        try:
            from langchain_together import ChatTogether

            model = ChatTogether(
                together_api_key=self.api_key,
                model=self.model_name,
                temperature=temperature,
            )
            response = model.invoke(prompt)
            return str(response.content).strip()
        except Exception as exc:
            raise ExternalServiceException("Together generation failed", details={"reason": str(exc)}) from exc


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
                groq_api_key=self.api_key,
                model=self.model_name,
                temperature=temperature,
            )

            messages: list[tuple[str, str]] = []
            if system_prompt:
                messages.append(("system", system_prompt))
            messages.append(("human", prompt))

            response = model.invoke(messages)
            return str(response.content).strip()
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
