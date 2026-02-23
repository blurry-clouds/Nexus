from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from loguru import logger

if TYPE_CHECKING:
    from main import NexusBot


class EventsCog(commands.Cog):
    def __init__(self, bot: "NexusBot") -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if self.bot.user:
            logger.info(
                "bot.connected",
                username=str(self.bot.user),
                user_id=self.bot.user.id,
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        preview = message.content.replace("\n", " ").strip()
        if len(preview) > 180:
            preview = preview[:177] + "..."

        self.bot.add_recent_message(
            message.channel.id,
            f"{message.author.display_name}: {preview}",
        )

        logger.debug(
            "event_router.received_message",
            guild_id=getattr(message.guild, "id", None),
            channel_id=message.channel.id,
            user_id=message.author.id,
        )
