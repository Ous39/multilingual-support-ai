from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

STOPWORDS = {
    "a", "an", "and", "are", "at", "de", "des", "du", "en", "et", "for", "i",
    "is", "je", "la", "le", "les", "my", "of", "on", "the", "to", "un", "une",
    "what", "with", "ci", "laa", "lan", "lu", "sama", "te", "wall", "walla",
}


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[\wÀ-ÿ]+", text.lower())
        if token not in STOPWORDS and len(token) > 1
    ]


@dataclass(frozen=True)
class KnowledgeDocument:
    id: str
    category: str
    title: dict[str, str]
    content: dict[str, str]


@dataclass(frozen=True)
class SearchResult:
    document: KnowledgeDocument
    score: float


class BM25Retriever:
    def __init__(self, documents: list[KnowledgeDocument], k1: float = 1.5, b: float = 0.75):
        self.documents = documents
        self.k1 = k1
        self.b = b
        self.corpora = [
            tokenize(" ".join(doc.title.values()) + " " + " ".join(doc.content.values()))
            for doc in documents
        ]
        self.lengths = [len(tokens) for tokens in self.corpora]
        self.avg_length = sum(self.lengths) / max(len(self.lengths), 1)
        self.term_frequencies = [Counter(tokens) for tokens in self.corpora]
        self.document_frequency = Counter(
            token for tokens in self.corpora for token in set(tokens)
        )

    @classmethod
    def from_json(cls, path: Path) -> BM25Retriever:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls([KnowledgeDocument(**item) for item in raw])

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        query_tokens = tokenize(query)
        scores: list[SearchResult] = []
        total_docs = len(self.documents)
        for index, document in enumerate(self.documents):
            score = 0.0
            frequencies = self.term_frequencies[index]
            length = self.lengths[index]
            for token in query_tokens:
                frequency = frequencies[token]
                if frequency == 0:
                    continue
                doc_frequency = self.document_frequency[token]
                idf = math.log(1 + (total_docs - doc_frequency + 0.5) / (doc_frequency + 0.5))
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * length / max(self.avg_length, 1)
                )
                score += idf * frequency * (self.k1 + 1) / denominator
            scores.append(SearchResult(document=document, score=score))

        ranked = sorted(scores, key=lambda item: item.score, reverse=True)[:top_k]
        if not ranked or ranked[0].score <= 0:
            return []
        return [
            SearchResult(document=item.document, score=round(1 - math.exp(-item.score / 2.5), 4))
            for item in ranked
            if item.score > 0
        ]
