from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.llm import build_generator
from app.metrics import metrics
from app.models import ChatRequest, ChatResponse, EvaluationRequest, EvaluationResponse
from app.retrieval import BM25Retriever
from app.safety import response_is_safe
from app.service import SupportService


@asynccontextmanager
async def lifespan(application: FastAPI):
    retriever = BM25Retriever.from_json(settings.knowledge_base_path)
    application.state.service = SupportService(settings, retriever, build_generator(settings))
    yield


app = FastAPI(
    title="Multilingual Support AI",
    description="A grounded, safety-aware multilingual support assistant reference implementation.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "provider": settings.llm_provider}


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await app.state.service.answer(request)


@app.post("/v1/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest) -> EvaluationResponse:
    result = await app.state.service.answer(
        ChatRequest(message=request.question, language=request.language)
    )
    retrieved_ids = {citation.document_id for citation in result.citations}
    retrieval_hit = not request.expected_document_ids or bool(
        retrieved_ids.intersection(request.expected_document_ids)
    )
    citation_present = bool(result.citations) or result.escalated
    safe = response_is_safe(result.answer)
    return EvaluationResponse(
        passed=retrieval_hit and citation_present and safe,
        retrieval_hit=retrieval_hit,
        citation_present=citation_present,
        safe_response=safe,
        confidence=result.confidence,
        latency_ms=result.latency_ms,
        answer=result.answer,
    )


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics() -> str:
    return metrics.render_prometheus()
