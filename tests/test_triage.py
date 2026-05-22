"""Tests for the triage engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from support_agent.core.triage import TriageEngine, PRIORITY_MAP, CATEGORIES


@pytest.fixture
def mock_mimo():
    mimo = MagicMock()
    mimo.complete = AsyncMock()
    return mimo


@pytest.fixture
def triage(mock_mimo):
    return TriageEngine(mock_mimo)


class TestTriageEngine:
    @pytest.mark.asyncio
    async def test_classify_critical_ticket(self, triage, mock_mimo):
        mock_mimo.complete.return_value = '{"priority": "P0", "category": "security", "confidence": 0.95, "reasoning": "Security breach detected"}'
        
        ticket = MagicMock()
        ticket.subject = "SECURITY ALERT: Unauthorized access"
        ticket.body = "Multiple failed login attempts detected from unknown IPs"
        ticket.ticket_id = "TKT-001"

        result = await triage.classify(ticket)
        assert result["priority"] == "P0"
        assert result["category"] == "security"
        assert result["confidence"] == 0.95
        assert result["sla_hours"] == 1

    @pytest.mark.asyncio
    async def test_classify_low_priority(self, triage, mock_mimo):
        mock_mimo.complete.return_value = '{"priority": "P3", "category": "feature_request", "confidence": 0.8, "reasoning": "Feature suggestion"}'
        
        ticket = MagicMock()
        ticket.subject = "Suggestion: dark mode"
        ticket.body = "Would be nice to have dark mode support"
        ticket.ticket_id = "TKT-002"

        result = await triage.classify(ticket)
        assert result["priority"] == "P3"
        assert result["category"] == "feature_request"
        assert result["sla_hours"] == 72

    @pytest.mark.asyncio
    async def test_classify_invalid_json_fallback(self, triage, mock_mimo):
        mock_mimo.complete.return_value = "This is not JSON"
        
        ticket = MagicMock()
        ticket.subject = "Test"
        ticket.body = "Test"
        ticket.ticket_id = "TKT-003"

        result = await triage.classify(ticket)
        assert result["priority"] == "P2"
        assert result["category"] == "general"
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_classify_api_error_fallback(self, triage, mock_mimo):
        mock_mimo.complete.side_effect = Exception("API Error")
        
        ticket = MagicMock()
        ticket.subject = "Test"
        ticket.body = "Test"
        ticket.ticket_id = "TKT-004"

        result = await triage.classify(ticket)
        assert result["priority"] == "P2"
        assert result["category"] == "general"

    def test_priority_map_complete(self):
        for p in ["P0", "P1", "P2", "P3"]:
            assert p in PRIORITY_MAP
            assert "label" in PRIORITY_MAP[p]
            assert "sla_hours" in PRIORITY_MAP[p]

    def test_categories_covered(self):
        expected = ["billing", "technical", "account", "feature_request", "bug_report", "security", "integration", "general"]
        for cat in expected:
            assert cat in CATEGORIES
