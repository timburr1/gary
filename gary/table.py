"""The game table: one LoreKit GameSession and the players talking to it."""

from __future__ import annotations

import asyncio
from pathlib import Path

from lorekit.orchestrator import GameSession

from gary.config import Config

DISCORD_GUIDE = Path(__file__).with_name("discord_guide.md")


def format_player_message(player: str, text: str) -> str:
    """Tag a message with its speaker so the GM can tell players apart."""
    return f"[{player}]: {text}"


class GameTable:
    def __init__(self, config: Config):
        self._session = GameSession(
            campaign_dir=config.campaign_dir,
            provider="claude",
            model=config.model,
            extra_guidelines=DISCORD_GUIDE.read_text(encoding="utf-8"),
        )
        # The GM agent is a single conversation, so turns go through one at a time.
        self._turn_lock = asyncio.Lock()
        self.ready = False

    async def start(self) -> None:
        await self._session.start()
        self.ready = True

    async def stop(self) -> None:
        self.ready = False
        await self._session.stop()

    async def take_turn(self, player: str, text: str) -> list[str]:
        """Send one player message to the GM and collect what should be posted back."""
        replies: list[str] = []
        async with self._turn_lock:
            async for event in self._session.send(format_player_message(player, text)):
                if event.type == "narration":
                    replies.append(event.content)
                elif event.type == "error":
                    replies.append(f"⚠️ {event.content}")
        return replies
