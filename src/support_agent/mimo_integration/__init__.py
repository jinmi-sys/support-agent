"""MiMo V2.5-Pro LLM integration."""

from support_agent.mimo_integration.client import MiMoClient
from support_agent.mimo_integration.prompts import (
    TRIAGE_SYSTEM_PROMPT,
    SENTIMENT_SYSTEM_PROMPT,
    RESOLUTION_SYSTEM_PROMPT,
)

__all__ = [
    "MiMoClient",
    "TRIAGE_SYSTEM_PROMPT",
    "SENTIMENT_SYSTEM_PROMPT",
    "RESOLUTION_SYSTEM_PROMPT",
]
