"""MiMo V2.5-Pro API client."""

from __future__ import annotations

import json
from typing import Any

import httpx

from support_agent.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_BASE_URL = "https://api.mimo.xiaomi.com/v1"
DEFAULT_MODEL = "MiMo-V2.5-Pro"


class MiMoClient:
    """Client for MiMo V2.5-Pro API."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", DEFAULT_BASE_URL).rstrip("/")
        self.model = config.get("model", DEFAULT_MODEL)
        self.max_tokens = config.get("max_tokens", 4096)
        self.default_temperature = config.get("temperature", 0.3)

    async def complete(
        self,
        system: str,
        user: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict[str, str] | None = None,
    ) -> str:
        """Send completion request to MiMo."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.default_temperature,
        }

        if response_format:
            payload["response_format"] = response_format

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                logger.info(
                    "mimo_completion",
                    model=self.model,
                    tokens_used=data.get("usage", {}).get("total_tokens", 0),
                )
                return content

        except httpx.HTTPStatusError as e:
            logger.error("mimo_api_error", status=e.response.status_code, body=e.response.text)
            raise
        except Exception as e:
            logger.error("mimo_request_failed", error=str(e))
            raise

    async def complete_json(
        self,
        system: str,
        user: str,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Send completion request and parse JSON response."""
        response = await self.complete(
            system=system,
            user=user,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return json.loads(response)

    async def health_check(self) -> bool:
        """Check if MiMo API is reachable."""
        try:
            await self.complete(
                system="Respond with 'ok'",
                user="ping",
                max_tokens=5,
                temperature=0.0,
            )
            return True
        except Exception:
            return False
