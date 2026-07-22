from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class Metrics:
    requests_total: int = 0
    escalations_total: int = 0
    blocked_total: int = 0
    latency_ms_total: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def record(self, latency_ms: int, escalated: bool = False, blocked: bool = False) -> None:
        with self._lock:
            self.requests_total += 1
            self.latency_ms_total += latency_ms
            self.escalations_total += int(escalated)
            self.blocked_total += int(blocked)

    def render_prometheus(self) -> str:
        with self._lock:
            average = self.latency_ms_total / max(self.requests_total, 1)
            return "\n".join(
                (
                    "# HELP support_requests_total Total support requests.",
                    "# TYPE support_requests_total counter",
                    f"support_requests_total {self.requests_total}",
                    "# HELP support_escalations_total Total escalated requests.",
                    "# TYPE support_escalations_total counter",
                    f"support_escalations_total {self.escalations_total}",
                    "# HELP support_blocked_total Total blocked unsafe requests.",
                    "# TYPE support_blocked_total counter",
                    f"support_blocked_total {self.blocked_total}",
                    "# HELP support_latency_ms_average Average request latency in milliseconds.",
                    "# TYPE support_latency_ms_average gauge",
                    f"support_latency_ms_average {average:.2f}",
                    "",
                )
            )


metrics = Metrics()
