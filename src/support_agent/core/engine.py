"""Core support engine - orchestrates triage, analysis, and resolution."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from support_agent.core.triage import TriageEngine
from support_agent.core.sentiment import SentimentAnalyzer
from support_agent.core.resolver import TicketResolver
from support_agent.knowledge.retriever import KnowledgeRetriever
from support_agent.mimo_integration.client import MiMoClient
from support_agent.utils.logger import get_logger
from support_agent.utils.metrics import MetricsCollector

logger = get_logger(__name__)


@dataclass
class Ticket:
    """Represents a support ticket."""

    ticket_id: str
    subject: str
    body: str
    channel: str
    customer_email: str = ""
    customer_name: str = ""
    priority: str = "P3"
    sentiment: str = "neutral"
    category: str = "general"
    status: str = "open"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None
    resolution: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Result of processing a ticket."""

    ticket_id: str
    priority: str
    sentiment: str
    category: str
    resolution: str
    confidence: float
    knowledge_hits: list[dict[str, Any]]
    processing_time_ms: float
    escalated: bool = False


class SupportEngine:
    """Main support engine orchestrating the full ticket lifecycle."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.mimo = MiMoClient(config.get("mimo", {}))
        self.triage = TriageEngine(self.mimo)
        self.sentiment = SentimentAnalyzer(self.mimo)
        self.knowledge = KnowledgeRetriever(config.get("knowledge", {}))
        self.resolver = TicketResolver(self.mimo, self.knowledge)
        self.metrics = MetricsCollector()
        self._tickets: dict[str, Ticket] = {}

    async def process_ticket(
        self,
        ticket_id: str | None = None,
        subject: str = "",
        body: str = "",
        channel: str = "email",
        customer_email: str = "",
        customer_name: str = "",
    ) -> dict[str, Any]:
        """Process a ticket through the full pipeline."""
        start_time = datetime.now(timezone.utc)
        ticket_id = ticket_id or f"TKT-{uuid.uuid4().hex[:8].upper()}"

        logger.info("processing_ticket", ticket_id=ticket_id, channel=channel)

        ticket = Ticket(
            ticket_id=ticket_id,
            subject=subject,
            body=body,
            channel=channel,
            customer_email=customer_email,
            customer_name=customer_name,
        )

        # Step 1: Triage
        triage_result = await self.triage.classify(ticket)
        ticket.priority = triage_result["priority"]
        ticket.category = triage_result["category"]

        logger.info(
            "triage_complete",
            ticket_id=ticket_id,
            priority=ticket.priority,
            category=ticket.category,
        )

        # Step 2: Sentiment Analysis
        sentiment_result = await self.sentiment.analyze(ticket.subject, ticket.body)
        ticket.sentiment = sentiment_result["label"]

        logger.info(
            "sentiment_complete",
            ticket_id=ticket_id,
            sentiment=ticket.sentiment,
        )

        # Step 3: Knowledge Retrieval
        knowledge_hits = await self.knowledge.retrieve(
            query=f"{ticket.subject} {ticket.body}",
            top_k=5,
        )

        # Step 4: Resolution
        resolution_result = await self.resolver.resolve(ticket, knowledge_hits)
        ticket.resolution = resolution_result["resolution"]
        ticket.confidence = resolution_result["confidence"]
        ticket.status = "resolved"
        ticket.resolved_at = datetime.now(timezone.utc)

        # Record metrics
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        self.metrics.record_ticket({
            "ticket_id": ticket_id,
            "priority": ticket.priority,
            "sentiment": ticket.sentiment,
            "channel": channel,
            "resolved": True,
            "response_time_ms": elapsed,
            "confidence": ticket.confidence,
        })

        self._tickets[ticket_id] = ticket

        logger.info(
            "ticket_resolved",
            ticket_id=ticket_id,
            confidence=ticket.confidence,
            elapsed_ms=elapsed,
        )

        return {
            "ticket_id": ticket_id,
            "priority": ticket.priority,
            "sentiment": ticket.sentiment,
            "category": ticket.category,
            "resolution": ticket.resolution,
            "confidence": ticket.confidence,
            "knowledge_hits": knowledge_hits,
            "processing_time_ms": elapsed,
            "escalated": resolution_result.get("escalated", False),
        }

    async def start_listener(self, channels: list[str]) -> None:
        """Start listening on specified channels."""
        from support_agent.channels import get_channel

        logger.info("starting_listener", channels=channels)

        listeners = []
        for ch_name in channels:
            channel = get_channel(ch_name, self.config.get("channels", {}).get(ch_name, {}))
            listeners.append(channel.listen(self._handle_incoming))

        await asyncio.gather(*listeners)

    async def _handle_incoming(self, message: dict[str, Any]) -> None:
        """Handle incoming message from any channel."""
        try:
            await self.process_ticket(
                subject=message.get("subject", ""),
                body=message.get("body", ""),
                channel=message.get("channel", "unknown"),
                customer_email=message.get("from", ""),
                customer_name=message.get("name", ""),
            )
        except Exception as e:
            logger.error("handle_incoming_failed", error=str(e))

    async def batch_triage(self, status: str = "pending") -> dict[str, Any]:
        """Run triage on all tickets with given status."""
        pending = [t for t in self._tickets.values() if t.status == status]
        count = 0
        for ticket in pending:
            result = await self.triage.classify(ticket)
            ticket.priority = result["priority"]
            ticket.category = result["category"]
            count += 1

        return {"count": count, "status": status}
