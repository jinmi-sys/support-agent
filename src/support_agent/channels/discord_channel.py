"""Discord support channel implementation."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Awaitable

from support_agent.channels import BaseChannel
from support_agent.utils.logger import get_logger

logger = get_logger(__name__)


class DiscordChannel(BaseChannel):
    """Discord bot support channel."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__("discord", config)
        self.token = config.get("token", "")
        self.support_channel_id = config.get("support_channel_id", "")

    async def listen(self, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        """Connect to Discord and listen for support messages."""
        logger.info("discord_listener_started")
        await self.on_connect()

        try:
            while True:
                # Discord bot connection would go here
                # Using discord.py or similar library
                # async for message in client:
                #     await handler({...})
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await self.on_disconnect()
        except Exception as e:
            logger.error("discord_listen_error", error=str(e))
            await self.on_disconnect()

    async def send(self, to: str, subject: str, body: str) -> bool:
        """Send Discord message."""
        logger.info("discord_sending", channel=to)
        try:
            # Discord send implementation would go here
            logger.info("discord_sent", channel=to)
            return True
        except Exception as e:
            logger.error("discord_send_failed", channel=to, error=str(e))
            return False
