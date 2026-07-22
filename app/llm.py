from __future__ import annotations

from typing import Protocol

import httpx

from app.config import Settings
from app.models import Language
from app.retrieval import SearchResult

FALLBACK_PREFIX = {
    "en": "Based on the support information available:",
    "fr": "D'après les informations d'assistance disponibles :",
    "wo": "Ci li nekk ci xibaar yi ñu am:",
}


class AnswerGenerator(Protocol):
    async def generate(self, question: str, language: Language, context: list[SearchResult]) -> str:
        ...


class ExtractiveAnswerGenerator:
    async def generate(self, question: str, language: Language, context: list[SearchResult]) -> str:
        del question
        if not context:
            return ""
        passages = [
            item.document.content.get(language) or item.document.content["en"]
            for item in context[:2]
        ]
        return f"{FALLBACK_PREFIX[language]} " + " ".join(passages)


class OpenAICompatibleAnswerGenerator:
    def __init__(self, settings: Settings):
        if not settings.llm_api_key:
            raise ValueError(
                "LLM_API_KEY or OPENAI_API_KEY is required for the configured provider"
            )
        self.settings = settings

    async def generate(self, question: str, language: Language, context: list[SearchResult]) -> str:
        context_text = "\n\n".join(
            f"[{item.document.id}] "
            f"{item.document.content.get(language) or item.document.content['en']}"
            for item in context
        )
        system = (
            "You are a financial-services support assistant. Answer only from the supplied "
            "context. Never request a PIN, OTP, password, or full account number. If the "
            "context is insufficient, "
            "say you cannot confirm and recommend human support. Keep the answer concise. "
            f"Answer in language code {language}. Cite source IDs in square brackets."
        )
        payload = {
            "model": self.settings.llm_model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}"},
            ],
        }
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return str(data["choices"][0]["message"]["content"]).strip()


def build_generator(settings: Settings) -> AnswerGenerator:
    if settings.llm_provider.lower() in {"openai", "openai-compatible"}:
        return OpenAICompatibleAnswerGenerator(settings)
    return ExtractiveAnswerGenerator()
