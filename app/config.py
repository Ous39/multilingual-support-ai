from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Multilingual Support AI"
    environment: str = os.getenv("APP_ENV", "development")
    knowledge_base_path: Path = Path(
        os.getenv("KNOWLEDGE_BASE_PATH", str(ROOT_DIR / "data" / "knowledge_base.json"))
    )
    llm_provider: str = os.getenv("LLM_PROVIDER", "extractive")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_api_key: str | None = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "3"))
    min_confidence: float = float(os.getenv("MIN_CONFIDENCE", "0.26"))
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))


settings = Settings()
