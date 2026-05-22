"""Support metrics tracking and analytics."""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any


class MetricsCollector:
    """Collects and aggregates support metrics."""

    def __init__(self) -> None:
        self._tickets: list[dict[str, Any]] = []
        self._counters: dict[str, int] = defaultdict(int)
        self._start_time = time.monotonic()

    def record_ticket(self, ticket_data: dict[str, Any]) -> None:
        """Record a processed ticket for metrics."""
        ticket_data["recorded_at"] = datetime.now(timezone.utc).isoformat()
        self._tickets.append(ticket_data)
        self._counters["total_tickets"] += 1

        priority = ticket_data.get("priority", "P3")
        self._counters[f"priority_{priority}"] += 1

        channel = ticket_data.get("channel", "unknown")
        self._counters[f"channel_{channel}"] += 1

        if ticket_data.get("resolved"):
            self._counters["resolved"] += 1

    def get_summary(self, period: str = "24h") -> dict[str, Any]:
        """Get metrics summary for time period."""
        cutoff = self._period_cutoff(period)
        relevant = [
            t for t in self._tickets
            if self._parse_time(t.get("recorded_at")) >= cutoff
        ]

        total = len(relevant)
        resolved = sum(1 for t in relevant if t.get("resolved"))
        response_times = [t.get("response_time_ms", 0) for t in relevant]
        confidences = [t.get("confidence", 0) for t in relevant]

        return {
            "total_tickets": total,
            "resolved_tickets": resolved,
            "resolution_rate": resolved / total if total > 0 else 0.0,
            "avg_response_time": sum(response_times) / total / 1000 if total > 0 else 0.0,
            "avg_confidence": sum(confidences) / total if total > 0 else 0.0,
            "csat_score": min(5.0, max(1.0, (sum(confidences) / total * 5) if total > 0 else 3.5)),
            "priority_breakdown": self._breakdown(relevant, "priority"),
            "channel_breakdown": self._breakdown(relevant, "channel"),
            "period": period,
        }

    def _breakdown(self, tickets: list[dict[str, Any]], key: str) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for t in tickets:
            val = t.get(key, "unknown")
            if isinstance(val, str) and val.startswith("P"):
                counts[val] += 1
            else:
                val_str = str(val) if not isinstance(val, str) else val
                counts[val_str] += 1
        return dict(counts)

    def _period_cutoff(self, period: str) -> datetime:
        now = datetime.now(timezone.utc)
        offsets = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        return now - offsets.get(period, timedelta(hours=24))

    @staticmethod
    def _parse_time(ts: str | None) -> datetime:
        if not ts:
            return datetime.min.replace(tzinfo=timezone.utc)
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return datetime.min.replace(tzinfo=timezone.utc)
