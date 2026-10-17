"""Discord front end: relays chat in the game channel to the LoreKit GM."""

from __future__ import annotations

import logging
import random

import discord
from discord import app_commands
from dotenv import load_dotenv

from gary.config import Config, prepare_environment
from gary.discord_text import split_message
from gary.table import GameTable

log = logging.getLogger(__name__)


class Gary(discord.Client):
    def __init__(self, config: Config):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.config = config
        self.table = GameTable(config)
        self.tree = app_commands.CommandTree(self)
        self.tree.add_command(roll)

    async def setup_hook(self) -> None:
        # Guild commands show up immediately; global ones can take up to an hour.
        guild = discord.Object(id=self.config.guild_id) if self.config.guild_id else None
        if guild:
            self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        self.loop.create_task(self._open_table())

    async def _open_table(self) -> None:
        await self.wait_until_ready()
        channel = self.get_channel(self.config.game_channel_id)
        try:
            await self.table.start()
        except Exception:
            log.exception("Failed to start the LoreKit session")
            if channel:
                await channel.send("I couldn't start the game engine. Check the bot's console.")
            return
        log.info("Game table open")
        if channel:
            await channel.send("The GM is ready. Say something to begin.")

    async def on_ready(self) -> None:
        log.info("Logged in as %s", self.user)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.channel.id != self.config.game_channel_id:
            return
        if not message.content.strip():
            return
        if not self.table.ready:
            await message.reply("Still setting up the table, give me a moment.")
            return

        async with message.channel.typing():
            replies = await self.table.take_turn(message.author.display_name, message.content)
        for reply in replies:
            for chunk in split_message(reply):
                await message.channel.send(chunk)

    async def close(self) -> None:
        await self.table.stop()
        await super().close()


@app_commands.command(description="Roll a single die.")
@app_commands.describe(sides="Number of sides, e.g. 20 for a d20")
async def roll(interaction: discord.Interaction, sides: app_commands.Range[int, 2, 1000]) -> None:
    result = random.randint(1, sides)
    await interaction.response.send_message(f"🎲 {interaction.user.display_name} rolls a d{sides}: **{result}**")


def main() -> None:
    load_dotenv()
    discord.utils.setup_logging()
    config = Config.from_env()
    prepare_environment()
    Gary(config).run(config.discord_token, log_handler=None)
