"""Tests for sentiment analysis."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from support_agent.core.sentiment import SentimentAnalyzer, SENTIMENT_LABELS


@pytest.fixture
def mock_mimo():
    mimo = MagicMock()
    mimo.complete = AsyncMock()
    return mimo


@pytest.fixture
def analyzer(mock_mimo):
    return SentimentAnalyzer(mock_mimo)


class TestSentimentAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_positive(self, analyzer, mock_mimo):
        mock_mimo.complete.return_value = '{"label": "positive", "score": 0.85, "emotions": ["grateful", "happy"], "confidence": 0.92}'
        
        result = await analyzer.analyze("Thank you!", "Your support was amazing, resolved my issue quickly!")
        assert result["label"] == "positive"
        assert result["score"] == 0.85
        assert "grateful" in result["emotions"]
        assert result["emoji"] == "😊"

    @pytest.mark.asyncio
    async def test_analyze_angry(self, analyzer, mock_mimo):
        mock_mimo.complete.return_value = '{"label": "angry", "score": -0.9, "emotions": ["furious", "betrayed"], "confidence": 0.88}'
        
        result = await analyzer.analyze("THIS IS UNACCEPTABLE", "I have been waiting for 3 WEEKS!!! Fix this NOW or I'm suing!")
        assert result["label"] == "angry"
        assert result["score"] == -0.9
        assert result["emoji"] == "😡"

    @pytest.mark.asyncio
    async def test_analyze_neutral(self, analyzer, mock_mimo):
        mock_mimo.complete.return_value = '{"label": "neutral", "score": 0.0, "emotions": ["calm"], "confidence": 0.7}'
        
        result = await analyzer.analyze("Question about billing", "What is the billing cycle for monthly plans?")
        assert result["label"] == "neutral"
        assert result["emoji"] == "😐"

    @pytest.mark.asyncio
    async def test_analyze_frustrated(self, analyzer, mock_mimo):
        mock_mimo.complete.return_value = '{"label": "frustrated", "score": -0.3, "emotions": ["frustrated", "impatient"], "confidence": 0.85}'
        
        result = await analyzer.analyze("Still not working", "This is the third time I've contacted support about the same issue...")
        assert result["label"] == "frustrated"
        assert result["emoji"] == "😤"

    @pytest.mark.asyncio
    async def test_analyze_invalid_json_fallback(self, analyzer, mock_mimo):
        mock_mimo.complete.return_value = "Not valid JSON"
        
        result = await analyzer.analyze("Test", "Test body")
        assert result["label"] == "neutral"
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_analyze_api_error_fallback(self, analyzer, mock_mimo):
        mock_mimo.complete.side_effect = Exception("API Down")
        
        result = await analyzer.analyze("Test", "Test body")
        assert result["label"] == "neutral"

    @pytest.mark.asyncio
    async def test_analyze_turn_multiple_messages(self, analyzer, mock_mimo):
        mock_mimo.complete.return_value = '{"label": "confused", "score": 0.1, "emotions": ["confused"], "confidence": 0.75}'
        
        messages = [
            {"role": "user", "content": "I need help with my account"},
            {"role": "agent", "content": "Sure, what seems to be the issue?"},
            {"role": "user", "content": "I don't understand the error message"},
        ]
        result = await analyzer.analyze_turn(messages)
        assert result["label"] == "confused"

    def test_sentiment_labels_complete(self):
        expected = ["positive", "neutral", "frustrated", "angry", "confused"]
        for label in expected:
            assert label in SENTIMENT_LABELS
            assert "emoji" in SENTIMENT_LABELS[label]
            assert "score_range" in SENTIMENT_LABELS[label]
