"""Settings read from .env, plus the environment LoreKit's subprocesses need."""

from __future__ import annotations

import logging
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    discord_token: str
    game_channel_id: int
    guild_id: int | None
    model: str
    campaign_dir: Path

    @classmethod
    def from_env(cls) -> Config:
        missing = [k for k in ("DISCORD_TOKEN", "GAME_CHANNEL_ID") if not os.environ.get(k)]
        if missing:
            sys.exit(f"Missing required settings in .env: {', '.join(missing)}")

        guild_id = os.environ.get("GUILD_ID")
        return cls(
            discord_token=os.environ["DISCORD_TOKEN"],
            game_channel_id=int(os.environ["GAME_CHANNEL_ID"]),
            guild_id=int(guild_id) if guild_id else None,
            model=os.environ.get("GARY_MODEL", "opus"),
            campaign_dir=Path(os.environ.get("GARY_CAMPAIGN_DIR", PROJECT_ROOT / "campaign")),
        )


def prepare_environment() -> None:
    """Set env vars that LoreKit's MCP server and Claude subprocesses inherit."""
    # LoreKit opens its JSON/Markdown data without an explicit encoding; on
    # Windows that means cp1252 unless the child interpreters run in UTF-8 mode.
    os.environ.setdefault("PYTHONUTF8", "1")

    if "LOREKIT_CLAUDE_BIN" not in os.environ:
        claude = _find_claude()
        if claude:
            os.environ["LOREKIT_CLAUDE_BIN"] = claude

    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.warning("ANTHROPIC_API_KEY is not set; Claude Code will fall back to whatever account it is logged in with.")


def _find_claude() -> str | None:
    found = shutil.which("claude")
    if not found:
        return None
    # npm installs a claude.cmd shim on Windows, which subprocess can't run
    # without a shell. The real binary ships inside the package.
    if found.lower().endswith(".cmd"):
        exe = Path(found).parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
        if exe.is_file():
            return str(exe)
    return found
