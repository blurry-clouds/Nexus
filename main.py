import asyncio
from collections import defaultdict, deque
from typing import Deque, DefaultDict

import discord
from discord.ext import commands
from loguru import logger

from brain.claude_client import ClaudeClient
from brain.decision_engine import DecisionEngine
from cogs.autonomous import AutonomousCog
from cogs.commands import CommandsCog
from cogs.events import EventsCog
from cogs.moderation import ModerationCog
from config import get_settings


class NexusBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(command_prefix="!", intents=intents)

        self.recent_messages: DefaultDict[int, Deque[str]] = defaultdict(lambda: deque(maxlen=10))
        self.claude_client = ClaudeClient()
        self.decision_engine = DecisionEngine(self.claude_client)

    def add_recent_message(self, channel_id: int, formatted_message: str) -> None:
        self.recent_messages[channel_id].append(formatted_message)

    def get_recent_messages(self, channel_id: int) -> list[str]:
        return list(self.recent_messages[channel_id])

    async def setup_hook(self) -> None:
        await self.add_cog(EventsCog(self))
        await self.add_cog(ModerationCog(self))
        await self.add_cog(AutonomousCog(self))
        await self.add_cog(CommandsCog(self))
        await self.tree.sync()
        logger.info("slash_commands.synced")


async def main() -> None:
    settings = get_settings()
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=settings.log_level,
        serialize=True,
    )

    if not settings.discord_token:
        raise RuntimeError("DISCORD_TOKEN is not configured in .env")

    bot = NexusBot()
    await bot.start(settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())
