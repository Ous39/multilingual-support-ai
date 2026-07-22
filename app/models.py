from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Language = Literal["en", "fr", "wo"]


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2_000)
    language: Language | None = None
    session_id: str | None = Field(default=None, max_length=100)


class Citation(BaseModel):
    document_id: str
    title: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    language: Language
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[Citation]
    escalated: bool
    escalation_reason: str | None = None
    pii_redacted: bool = False
    latency_ms: int


class EvaluationRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2_000)
    expected_document_ids: list[str] = Field(default_factory=list)
    language: Language | None = None


class EvaluationResponse(BaseModel):
    passed: bool
    retrieval_hit: bool
    citation_present: bool
    safe_response: bool
    confidence: float
    latency_ms: int
    answer: str
