"""Tests for the support engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from support_agent.core.engine import SupportEngine, Ticket


@pytest.fixture
def mock_config():
    return {
        "mimo": {"api_key": "test", "model": "MiMo-V2.5-Pro"},
        "knowledge": {"embedding_model": "test", "top_k": 3},
        "channels": {},
        "database": {"url": "sqlite:///:memory:"},
        "redis": {"url": "redis://localhost:6379/0"},
    }


@pytest.fixture
def engine(mock_config):
    with patch("support_agent.core.engine.MiMoClient") as mock_mimo, \
         patch("support_agent.core.engine.TriageEngine") as mock_triage, \
         patch("support_agent.core.engine.SentimentAnalyzer") as mock_sentiment, \
         patch("support_agent.core.engine.KnowledgeRetriever") as mock_kb, \
         patch("support_agent.core.engine.TicketResolver") as mock_resolver:
        
        mock_triage.return_value.classify = AsyncMock(
            return_value={"priority": "P1", "category": "billing", "confidence": 0.9}
        )
        mock_sentiment.return_value.analyze = AsyncMock(
            return_value={"label": "frustrated", "score": -0.3, "emotions": ["frustrated"], "confidence": 0.85}
        )
        mock_kb.return_value.retrieve = AsyncMock(
            return_value=[{"title": "Refund Policy", "content": "Refunds are processed in 3-5 days.", "relevance_score": 0.92}]
        )
        mock_resolver.return_value.resolve = AsyncMock(
            return_value={"resolution": "Your refund is being processed.", "confidence": 0.88, "escalated": False}
        )

        eng = SupportEngine(mock_config)
        yield eng


class TestSupportEngine:
    @pytest.mark.asyncio
    async def test_process_ticket_returns_result(self, engine):
        result = await engine.process_ticket(
            subject="Refund not received",
            body="I requested a refund 5 days ago and haven't received it.",
            channel="email",
            customer_email="user@test.com",
        )

        assert "ticket_id" in result
        assert result["priority"] == "P1"
        assert result["sentiment"] == "frustrated"
        assert result["category"] == "billing"
        assert result["confidence"] == 0.88
        assert result["processing_time_ms"] > 0

    @pytest.mark.asyncio
    async def test_process_ticket_records_metrics(self, engine):
        await engine.process_ticket(
            subject="Test ticket",
            body="Test body",
            channel="chat",
        )
        
        summary = engine.metrics.get_summary("24h")
        assert summary["total_tickets"] >= 1

    @pytest.mark.asyncio
    async def test_batch_triage(self, engine):
        engine._tickets["TKT-001"] = Ticket(
            ticket_id="TKT-001",
            subject="Test",
            body="Test body",
            channel="email",
            status="pending",
        )
        
        result = await engine.batch_triage("pending")
        assert result["count"] >= 0


class TestTicket:
    def test_ticket_defaults(self):
        ticket = Ticket(
            ticket_id="TKT-001",
            subject="Test",
            body="Body",
            channel="email",
        )
        assert ticket.priority == "P3"
        assert ticket.sentiment == "neutral"
        assert ticket.status == "open"
        assert ticket.confidence == 0.0

    def test_ticket_custom_values(self):
        ticket = Ticket(
            ticket_id="TKT-002",
            subject="Urgent",
            body="Server down",
            channel="chat",
            priority="P0",
            sentiment="angry",
        )
        assert ticket.priority == "P0"
        assert ticket.sentiment == "angry"
