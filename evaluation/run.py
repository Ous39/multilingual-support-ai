from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx


async def run(base_url: str) -> int:
    dataset = Path(__file__).with_name("golden_set.jsonl")
    cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line]
    passed = 0
    latencies: list[int] = []
    async with httpx.AsyncClient(base_url=base_url, timeout=30) as client:
        for case in cases:
            response = await client.post("/v1/evaluate", json=case)
            response.raise_for_status()
            result = response.json()
            passed += int(result["passed"])
            latencies.append(result["latency_ms"])
            marker = "PASS" if result["passed"] else "FAIL"
            print(f"{marker} | {case['language']} | {case['question']}")

    pass_rate = passed / len(cases)
    average_latency = sum(latencies) / len(latencies)
    print(f"\nPass rate: {pass_rate:.1%} ({passed}/{len(cases)})")
    print(f"Average latency: {average_latency:.1f} ms")
    return 0 if pass_rate >= 0.90 else 1


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    raise SystemExit(asyncio.run(run(url)))
