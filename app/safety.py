from __future__ import annotations

import re
from dataclasses import dataclass

INJECTION_PATTERNS = (
    r"ignore (all |the )?(previous|prior|system) instructions",
    r"reveal (the )?(system prompt|hidden instructions|api key|secret)",
    r"developer message",
    r"act as .* without restrictions",
)

PII_PATTERNS = (
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"(?<!\w)(?:\+?\d[\d\s-]{7,}\d)(?!\w)"),
    re.compile(r"\b(?:pin|otp|password)\s*[:=-]?\s*\w+", re.IGNORECASE),
)


@dataclass(frozen=True)
class SafetyResult:
    safe_text: str
    pii_redacted: bool
    blocked: bool
    reason: str | None = None


def inspect_and_redact(text: str) -> SafetyResult:
    lowered = text.lower()
    if any(re.search(pattern, lowered) for pattern in INJECTION_PATTERNS):
        return SafetyResult(
            safe_text="",
            pii_redacted=False,
            blocked=True,
            reason="Potential prompt-injection attempt detected",
        )

    redacted = text
    for pattern in PII_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return SafetyResult(
        safe_text=redacted,
        pii_redacted=redacted != text,
        blocked=False,
    )


def response_is_safe(text: str) -> bool:
    lowered = text.lower()
    forbidden = ("api_key=", "bearer token", "system prompt:", "password is")
    return not any(item in lowered for item in forbidden)
