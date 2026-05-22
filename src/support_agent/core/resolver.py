"""Autonomous ticket resolution with knowledge base integration."""

from __future__ import annotations

from typing import Any

from support_agent.mimo_integration.client import MiMoClient
from support_agent.mimo_integration.prompts import RESOLUTION_SYSTEM_PROMPT
from support_agent.knowledge.retriever import KnowledgeRetriever
from support_agent.utils.logger import get_logger

logger = get_logger(__name__)

ESCALATION_THRESHOLDS = {
    "P0": 0.5,  # Escalate if confidence < 50%
    "P1": 0.4,
    "P2": 0.3,
    "P3": 0.2,
}


class TicketResolver:
    """Resolves tickets autonomously using MiMo and knowledge base."""

    def __init__(self, mimo: MiMoClient, knowledge: KnowledgeRetriever) -> None:
        self.mimo = mimo
        self.knowledge = knowledge

    async def resolve(
        self,
        ticket: Any,
        knowledge_hits: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate resolution for a ticket."""
        context = self._build_context(ticket, knowledge_hits)
        priority = getattr(ticket, "priority", "P3")

        try:
            response = await self.mimo.complete(
                system=RESOLUTION_SYSTEM_PROMPT,
                user=context,
                temperature=0.3,
                max_tokens=2000,
            )

            result = self._parse_response(response, priority)
            logger.info(
                "resolution_generated",
                ticket_id=getattr(ticket, "ticket_id", "unknown"),
                confidence=result["confidence"],
                escalated=result.get("escalated", False),
            )
            return result

        except Exception as e:
            logger.error("resolution_failed", error=str(e))
            return {
                "resolution": "Unable to auto-resolve. Escalating to human agent.",
                "confidence": 0.0,
                "escalated": True,
            }

    def _build_context(self, ticket: Any, knowledge_hits: list[dict[str, Any]]) -> str:
        kb_context = ""
        if knowledge_hits:
            kb_sections = []
            for i, hit in enumerate(knowledge_hits[:5], 1):
                kb_sections.append(f"[KB Article {i}] {hit.get('title', 'Untitled')}\n{hit.get('content', '')}")
            kb_context = "\n\n".join(kb_sections)

        subject = getattr(ticket, "subject", "")
        body = getattr(ticket, "body", "")
        priority = getattr(ticket, "priority", "P3")
        category = getattr(ticket, "category", "general")
        sentiment = getattr(ticket, "sentiment", "neutral")

        return f"""Resolve this support ticket:

**Ticket Details:**
- Subject: {subject}
- Body: {body}
- Priority: {priority}
- Category: {category}
- Customer Sentiment: {sentiment}

**Relevant Knowledge Base Articles:**
{kb_context or "No relevant articles found."}

Provide a resolution in JSON format:
{{"resolution": "<detailed resolution text>", "confidence": <0.0-1.0>, "steps": ["step1", "step2"], "escalate": false}}"""

    def _parse_response(self, response: str, priority: str) -> dict[str, Any]:
        import json
        try:
            data = json.loads(response)
            confidence = float(data.get("confidence", 0.5))
            threshold = ESCALATION_THRESHOLDS.get(priority, 0.3)
            should_escalate = data.get("escalate", False) or confidence < threshold

            return {
                "resolution": data.get("resolution", ""),
                "confidence": confidence,
                "steps": data.get("steps", []),
                "escalated": should_escalate,
            }
        except (json.JSONDecodeError, ValueError):
            return {
                "resolution": response,
                "confidence": 0.3,
                "steps": [],
                "escalated": True,
            }
