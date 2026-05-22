"""Multi-channel support abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Awaitable

from support_agent.utils.logger import get_logger

logger = get_logger(__name__)


class BaseChannel(ABC):
    """Base class for support channels."""

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config

    @abstractmethod
    async def listen(self, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        """Listen for incoming messages and pass to handler."""
        ...

    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> bool:
        """Send a message to a customer."""
        ...

    async def on_connect(self) -> None:
        logger.info("channel_connected", channel=self.name)

    async def on_disconnect(self) -> None:
        logger.info("channel_disconnected", channel=self.name)


def get_channel(name: str, config: dict[str, Any]) -> BaseChannel:
    """Factory to get channel instance by name."""
    from support_agent.channels.email_channel import EmailChannel
    from support_agent.channels.chat_channel import ChatChannel
    from support_agent.channels.discord_channel import DiscordChannel

    channels = {
        "email": EmailChannel,
        "chat": ChatChannel,
        "discord": DiscordChannel,
    }

    if name not in channels:
        raise ValueError(f"Unknown channel: {name}. Available: {list(channels.keys())}")

    return channels[name](config)
