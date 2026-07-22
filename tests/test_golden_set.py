from __future__ import annotations

import json
from pathlib import Path


def test_golden_retrieval_set(client):
    dataset = Path(__file__).resolve().parents[1] / "evaluation" / "golden_set.jsonl"
    cases = [
        json.loads(line)
        for line in dataset.read_text(encoding="utf-8").splitlines()
        if line
    ]

    outcomes = [
        client.post("/v1/evaluate", json=case).json()["passed"]
        for case in cases
    ]

    assert sum(outcomes) / len(outcomes) >= 0.90
