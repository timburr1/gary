"""Fitting GM output into Discord's 2,000-character message limit."""

from __future__ import annotations

DISCORD_LIMIT = 2000


def split_message(text: str, limit: int = DISCORD_LIMIT) -> list[str]:
    """Split text into chunks of at most `limit` chars, preferring paragraph, then line, then word breaks."""
    chunks: list[str] = []
    rest = text.strip()
    while len(rest) > limit:
        window = rest[:limit]
        cut = max(window.rfind("\n\n"), 0) or max(window.rfind("\n"), 0) or max(window.rfind(" "), 0) or limit
        chunks.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    if rest:
        chunks.append(rest)
    return chunks
