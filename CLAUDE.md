# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Gary is a Discord bot that runs a Pathfinder 2e campaign. It's a thin client:
the game master is a [LoreKit](https://github.com/matluz1/lorekit) `GameSession`,
which runs a Claude Code agent (`claude -p`) as the GM and keeps campaign state
in SQLite. Gary relays chat between one Discord channel and that GM. Solo play
for now; six-player support (free-form chat, turn-based combat) is the planned
next step, so avoid baking in single-player assumptions.

## Commands

```
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt          # pulls torch via sentence-transformers; large
python -m gary                           # run the bot (needs .env, see .env.example)
python -m pytest -q tests                # all tests
python -m pytest -q tests/test_discord_text.py::test_player_tag   # one test
```

The tests cover only pure helpers; nothing exercises Discord or LoreKit.
Starting a real GM turn spends API money.

## How it fits together

Process tree at runtime:

```
python -m gary                      (discord.py client, gary/bot.py)
├── python -m lorekit.server --http (MCP server on 127.0.0.1:3847, loads embedding model before binding)
│   └── claude -p ... (ephemeral)   (one per NPC line/turn, spawned by npc_interact / npc_combat_turn)
└── claude -p ... (persistent)      (the GM agent; talks to the MCP server, stdin/stdout stream-json)
```

- `gary/bot.py`: Discord side. Plain messages in `GAME_CHANNEL_ID` go to
  `GameTable.take_turn`. `/roll` is local only and never reaches the GM. The
  table starts in a background task after login, and messages are rejected
  until `table.ready`.
- `gary/table.py`: owns the `GameSession`. Messages are tagged
  `[Display Name]: text` and serialized through an `asyncio.Lock`, because
  the GM is a single conversation. Only `narration` and `error` events are
  posted back.
- `gary/discord_guide.md`: appended to LoreKit's GM system prompt via
  `GameSession(extra_guidelines=...)`. Client-specific GM behavior (forcing
  `pf2e`, Discord formatting, narrative voice, what commands exist) belongs
  here, not in code. The base GM rules live in `vendor/lorekit/guidelines/`.
- `gary/config.py`: `.env` → `Config`, plus `prepare_environment()`, which sets
  env vars that LoreKit's **child processes** inherit (`PYTHONUTF8=1`,
  `LOREKIT_CLAUDE_BIN`). Anything that has to affect the MCP server or the
  NPC agents must go through the environment, because a monkeypatch in the
  bot process won't reach them.

`ANTHROPIC_API_KEY` from `.env` is inherited by the `claude` subprocesses,
which is how usage is billed. `GARY_MODEL` (default `opus`) is a Claude Code
model alias used for both the GM and the NPCs.

## Vendored LoreKit

`vendor/lorekit` is a copy of LoreKit at upstream commit `db83614`, committed
directly into this repo and installed in editable mode. All local patches are
in `src/lorekit/orchestrator.py` and `src/lorekit/providers/claude/provider.py`.
To see them, diff those two files against the same paths in a fresh upstream
clone checked out at `db83614`. LoreKit finds
`systems/` and `guidelines/` by walking up from its source directory, so it
must stay an editable install of this checkout; a wheel install loses them.

The patches fix Windows / Microsoft Store Python problems (the README lists
them all). Keep them in mind when changing LoreKit code or upgrading it:

- The system prompt goes in a file (`--system-prompt-file`). The GM guide is
  longer than Windows' 32,767-character command-line limit.
- `.mcp.json` is written to the campaign dir. Store Python redirects writes
  under `AppData\Local` into a sandbox that `claude.exe` can't see.
- The MCP server's stderr goes to `campaign/mcp-server.log`, not an unread
  pipe that would eventually fill and block the server.
- The startup wait is 600 s, not 30 s, because of a cold embedding-model load.

`requirements.txt` pins `mcp==1.26.0`. LoreKit leaves it unpinned, and
mcp 2.x removed `FastMCP`.

## Runtime files

- `campaign/` (gitignored, override with `GARY_CAMPAIGN_DIR`): SQLite DB,
  `.mcp.json`, `mcp-server.log`.
- Killing the bot can leave `lorekit.server` and `claude.exe` children
  running. Kill the whole process tree (`taskkill /T`).
