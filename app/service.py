from __future__ import annotations

import time

from app.config import Settings
from app.language import detect_language
from app.llm import AnswerGenerator
from app.metrics import metrics
from app.models import ChatRequest, ChatResponse, Citation, Language
from app.retrieval import BM25Retriever
from app.safety import inspect_and_redact, response_is_safe

ESCALATION_MESSAGES: dict[Language, str] = {
    "en": (
        "I cannot confirm that from the available support information. "
        "I will refer you to a human support agent."
    ),
    "fr": (
        "Je ne peux pas le confirmer avec les informations disponibles. "
        "Je vais vous orienter vers un agent d'assistance."
    ),
    "wo": "Mënuma koo dëggal ci xibaar yi ñu am. Dinaa la jox ndimbal ci ab liggéeykat bu nit.",
}

BLOCKED_MESSAGES: dict[Language, str] = {
    "en": (
        "I cannot follow instructions that request secrets or attempt to override "
        "safety controls."
    ),
    "fr": (
        "Je ne peux pas suivre des instructions demandant des secrets ou contournant "
        "les contrôles de sécurité."
    ),
    "wo": "Mënuma topp ndigal buy laaj kumpa walla jéem a romb aar yi.",
}


class SupportService:
    def __init__(self, settings: Settings, retriever: BM25Retriever, generator: AnswerGenerator):
        self.settings = settings
        self.retriever = retriever
        self.generator = generator

    async def answer(self, request: ChatRequest) -> ChatResponse:
        started = time.perf_counter()
        language = request.language or detect_language(request.message)
        safety = inspect_and_redact(request.message)

        if safety.blocked:
            latency = self._latency(started)
            metrics.record(latency, escalated=True, blocked=True)
            return ChatResponse(
                answer=BLOCKED_MESSAGES[language],
                language=language,
                confidence=0,
                citations=[],
                escalated=True,
                escalation_reason=safety.reason,
                pii_redacted=False,
                latency_ms=latency,
            )

        results = self.retriever.search(safety.safe_text, self.settings.retrieval_top_k)
        confidence = results[0].score if results else 0.0
        if not results or confidence < self.settings.min_confidence:
            latency = self._latency(started)
            metrics.record(latency, escalated=True)
            return ChatResponse(
                answer=ESCALATION_MESSAGES[language],
                language=language,
                confidence=confidence,
                citations=[],
                escalated=True,
                escalation_reason="Insufficient grounded context",
                pii_redacted=safety.pii_redacted,
                latency_ms=latency,
            )

        answer = await self.generator.generate(safety.safe_text, language, results)
        if not answer or not response_is_safe(answer):
            answer = ESCALATION_MESSAGES[language]
            escalated = True
            reason = "Generated response failed safety validation"
        else:
            escalated = False
            reason = None

        latency = self._latency(started)
        metrics.record(latency, escalated=escalated)
        return ChatResponse(
            answer=answer,
            language=language,
            confidence=confidence,
            citations=[
                Citation(
                    document_id=item.document.id,
                    title=item.document.title.get(language) or item.document.title["en"],
                    score=item.score,
                )
                for item in results
            ],
            escalated=escalated,
            escalation_reason=reason,
            pii_redacted=safety.pii_redacted,
            latency_ms=latency,
        )

    @staticmethod
    def _latency(started: float) -> int:
        return max(1, round((time.perf_counter() - started) * 1_000))
