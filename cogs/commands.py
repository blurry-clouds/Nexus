from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from brain.decision_engine import AskContext
from config import get_settings

if TYPE_CHECKING:
    from main import NexusBot


class CommandsCog(commands.Cog):
    def __init__(self, bot: "NexusBot") -> None:
        self.bot = bot
        self.settings = get_settings()

    nexus = app_commands.Group(name="nexus", description="NEXUS slash command group")

    @nexus.command(name="ask", description="Ask NEXUS anything gaming related")
    async def ask(self, interaction: discord.Interaction, question: str) -> None:
        await interaction.response.defer(thinking=True)

        try:
            user_profile = (
                "No persisted profile loaded yet (DB models/queries are implemented in step 2)."
            )
            recent_messages = self.bot.get_recent_messages(interaction.channel_id)

            ask_ctx = AskContext(
                server_name=self.settings.server_name,
                username=interaction.user.display_name,
                user_id=interaction.user.id,
                channel_id=interaction.channel_id,
                user_profile=user_profile,
                recent_messages=recent_messages,
                question=question,
            )
            answer = await self.bot.decision_engine.answer_user_question(ask_ctx)
            await interaction.followup.send(answer)
        except Exception as exc:  # noqa: BLE001
            logger.exception("commands.ask.failed", error=str(exc))
            await interaction.followup.send(
                "NEXUS hit a runtime error while generating a response. "
                "Check provider config (AI_PROVIDER + related env vars).",
                ephemeral=True,
            )

    async def cog_load(self) -> None:
        self.bot.tree.add_command(self.nexus)
