from __future__ import annotations

from app.config import settings
from app.retrieval import BM25Retriever


def test_retriever_returns_expected_document():
    retriever = BM25Retriever.from_json(settings.knowledge_base_path)
    results = retriever.search("wrong recipient transfer reversal")
    assert results[0].document.id == "transfer-001"
    assert 0 < results[0].score <= 1


def test_retriever_returns_empty_for_unrelated_query():
    retriever = BM25Retriever.from_json(settings.knowledge_base_path)
    assert retriever.search("astronomy telescope galaxy") == []
