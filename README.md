# Gary
![](https://img.shields.io/github/repo-size/timburr1/gary)
![](https://img.shields.io/github/contributors/timburr1/gary)
![](https://img.shields.io/github/last-commit/timburr1/gary)

A Discord bot that runs a Pathfinder 2e campaign. The game master is a
[LoreKit](https://github.com/matluz1/lorekit) session: LoreKit runs a Claude
Code agent as the GM, keeps the campaign in SQLite, and does the rules math
deterministically. Gary relays chat between one Discord channel and that GM.

Currently built for solo play. Every message is tagged with the speaker's
display name, so the GM can already tell people apart.

## Setup

1. **Discord app.** In the [Developer Portal](https://discord.com/developers/applications),
   create an application. On the **Bot** tab, turn on **Message Content Intent**
   and copy the token. Under **OAuth2 > URL Generator**, tick `bot` and
   `applications.commands`, then the permissions *View Channels*, *Send
   Messages* and *Read Message History*. Open the URL to invite the bot.
2. **Claude Code** must be installed (`claude --version`). The GM and NPC
   agents run through it.
3. **Install** (Python 3.13+):
   ```
   python -m venv .venv
   .venv\Scripts\activate        # source .venv/bin/activate elsewhere
   pip install -r requirements.txt
   ```
   This pulls in sentence-transformers and torch, so it's a big download. The
   first run also downloads a ~500MB embedding model.
4. **Configure.** Copy `.env.example` to `.env` and fill it in.
5. **Run:** `python -m gary`

## Commands

- Plain chat in `GAME_CHANNEL_ID` goes to the GM.
- `/roll <sides>` rolls one die, e.g. `/roll 20`. It's a table toy: the GM
  never sees it and makes its own rolls.

## Vendored LoreKit

`vendor/lorekit` is a copy of LoreKit at upstream commit `db83614`, committed
directly into this repo. The local patches are all in
`src/lorekit/orchestrator.py` and `src/lorekit/providers/claude/provider.py`:

- The Claude system prompt goes in a file (`--system-prompt-file`), because
  the GM guidelines are longer than Windows' 32K command-line limit.
- `LOREKIT_CLAUDE_BIN` sets the path to the Claude binary. Gary fills it in
  automatically when npm's `claude.cmd` shim is all that's on PATH.
- The MCP server's stderr goes to `campaign/mcp-server.log` instead of a pipe
  that nothing reads, which would fill up and block the server.
- The startup wait is 10 minutes instead of 30 seconds. The server loads the
  embedding model before it binds its port, and a cold start can be slow.
- `.mcp.json` goes in the campaign dir instead of `AppData\Local\lorekit`.
  Microsoft Store Python redirects writes there into its sandbox, where
  `claude.exe` can't see them.

`requirements.txt` also pins `mcp==1.26.0`. LoreKit leaves `mcp` unpinned, and
2.x removed the `FastMCP` API it imports.
- `GameSession(extra_guidelines=...)` appends client-specific instructions to
  the GM prompt. Gary's are in [gary/discord_guide.md](gary/discord_guide.md).
