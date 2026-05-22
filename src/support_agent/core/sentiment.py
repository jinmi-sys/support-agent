"""Sentiment analysis engine powered by MiMo."""

from __future__ import annotations

from typing import Any

from support_agent.mimo_integration.client import MiMoClient
from support_agent.mimo_integration.prompts import SENTIMENT_SYSTEM_PROMPT
from support_agent.utils.logger import get_logger

logger = get_logger(__name__)

SENTIMENT_LABELS = {
    "positive": {"emoji": "😊", "score_range": (0.6, 1.0)},
    "neutral": {"emoji": "😐", "score_range": (0.4, 0.6)},
    "frustrated": {"emoji": "😤", "score_range": (-0.4, 0.0)},
    "angry": {"emoji": "😡", "score_range": (-1.0, -0.4)},
    "confused": {"emoji": "😕", "score_range": (0.0, 0.4)},
}


class SentimentAnalyzer:
    """Analyzes customer sentiment using MiMo."""

    def __init__(self, mimo: MiMoClient) -> None:
        self.mimo = mimo

    async def analyze(self, subject: str, body: str) -> dict[str, Any]:
        """Analyze sentiment of ticket content."""
        prompt = f"""Analyze the sentiment of this customer message:

Subject: {subject}
Body: {body}

Respond in JSON format:
{{"label": "positive|neutral|frustrated|angry|confused", "score": <-1.0 to 1.0>, "emotions": ["emotion1", "emotion2"], "confidence": <0.0-1.0>}}"""

        try:
            response = await self.mimo.complete(
                system=SENTIMENT_SYSTEM_PROMPT,
                user=prompt,
                temperature=0.1,
                max_tokens=300,
            )

            result = self._parse_response(response)
            logger.info("sentiment_analyzed", label=result["label"], score=result["score"])
            return result

        except Exception as e:
            logger.error("sentiment_failed", error=str(e))
            return {"label": "neutral", "score": 0.0, "emotions": [], "confidence": 0.0}

    async def analyze_turn(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Analyze sentiment across conversation turns."""
        combined = "\n".join(f"[{m.get('role', 'user')}]: {m.get('content', '')}" for m in messages)
        return await self.analyze("Conversation", combined)

    def _parse_response(self, response: str) -> dict[str, Any]:
        import json
        try:
            data = json.loads(response)
            label = data.get("label", "neutral").lower()
            if label not in SENTIMENT_LABELS:
                label = "neutral"
            return {
                "label": label,
                "score": float(data.get("score", 0.0)),
                "emotions": data.get("emotions", []),
                "confidence": float(data.get("confidence", 0.5)),
                "emoji": SENTIMENT_LABELS[label]["emoji"],
            }
        except (json.JSONDecodeError, ValueError):
            return {"label": "neutral", "score": 0.0, "emotions": [], "confidence": 0.0, "emoji": "😐"}
