"""Ticket priority classification using MiMo reasoning."""

from __future__ import annotations

from typing import Any

from support_agent.mimo_integration.client import MiMoClient
from support_agent.mimo_integration.prompts import TRIAGE_SYSTEM_PROMPT
from support_agent.utils.logger import get_logger

logger = get_logger(__name__)

PRIORITY_MAP = {
    "P0": {"label": "Critical", "sla_hours": 1, "description": "System down, data loss"},
    "P1": {"label": "High", "sla_hours": 4, "description": "Major feature broken"},
    "P2": {"label": "Medium", "sla_hours": 24, "description": "Partial functionality issue"},
    "P3": {"label": "Low", "sla_hours": 72, "description": "Question or minor issue"},
}

CATEGORIES = [
    "billing", "technical", "account", "feature_request",
    "bug_report", "security", "integration", "general",
]


class TriageEngine:
    """Classifies tickets by priority and category using MiMo."""

    def __init__(self, mimo: MiMoClient) -> None:
        self.mimo = mimo

    async def classify(self, ticket: Any) -> dict[str, Any]:
        """Classify a ticket's priority and category."""
        prompt = self._build_triage_prompt(ticket)

        try:
            response = await self.mimo.complete(
                system=TRIAGE_SYSTEM_PROMPT,
                user=prompt,
                temperature=0.1,
                max_tokens=500,
            )

            result = self._parse_response(response)
            logger.info(
                "triage_classified",
                ticket_id=getattr(ticket, "ticket_id", "unknown"),
                priority=result["priority"],
                category=result["category"],
            )
            return result

        except Exception as e:
            logger.error("triage_failed", error=str(e))
            return {"priority": "P2", "category": "general", "confidence": 0.0}

    def _build_triage_prompt(self, ticket: Any) -> str:
        subject = getattr(ticket, "subject", "")
        body = getattr(ticket, "body", "")
        return f"""Classify this support ticket:

Subject: {subject}
Body: {body}

Respond in JSON format:
{{"priority": "P0|P1|P2|P3", "category": "<category>", "confidence": <0.0-1.0>, "reasoning": "<brief explanation>"}}"""

    def _parse_response(self, response: str) -> dict[str, Any]:
        import json
        try:
            data = json.loads(response)
            priority = data.get("priority", "P2").upper()
            if priority not in PRIORITY_MAP:
                priority = "P2"
            category = data.get("category", "general")
            if category not in CATEGORIES:
                category = "general"
            return {
                "priority": priority,
                "category": category,
                "confidence": float(data.get("confidence", 0.5)),
                "reasoning": data.get("reasoning", ""),
                "sla_hours": PRIORITY_MAP[priority]["sla_hours"],
            }
        except (json.JSONDecodeError, ValueError):
            return {"priority": "P2", "category": "general", "confidence": 0.0}
