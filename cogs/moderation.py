from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import discord
from better_profanity import profanity
from discord.ext import commands
from loguru import logger

from brain.decision_engine import ModerationContext
from config import get_settings
from database.queries import add_mod_log, get_or_create_user
from database.session import AsyncSessionLocal

if TYPE_CHECKING:
    from main import NexusBot


class ModerationCog(commands.Cog):
    def __init__(self, bot: "NexusBot") -> None:
        self.bot = bot
        self.settings = get_settings()
        self._custom_flagged_words = {w.lower().strip() for w in self.settings.custom_flagged_words if w.strip()}
        profanity.load_censor_words()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        if not self._is_suspicious(message.content):
            return

        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(session, message.author.id, message.author.name)
            recent = self.bot.get_recent_messages(message.channel.id)
            user_profile = (
                f"username={user.username}; trust_score={user.trust_score}; "
                f"warnings={user.warning_count}; preferred_games={user.preferred_games}; notes={user.notes}"
            )

            decision = await self.bot.decision_engine.moderation_decision(
                ModerationContext(
                    server_name=self.settings.server_name,
                    username=message.author.display_name,
                    user_id=message.author.id,
                    channel_id=message.channel.id,
                    message_content=message.content,
                    user_profile=user_profile,
                    recent_messages=recent,
                    server_rules=self.settings.server_rules_text,
                )
            )

            if decision["confidence"] < self.settings.mod_confidence_threshold:
                await add_mod_log(
                    session,
                    user_id=message.author.id,
                    action="escalate",
                    reason=decision["reason"],
                    confidence=decision["confidence"],
                    message_content=message.content,
                    channel_id=message.channel.id,
                    mod_override=False,
                )
                await self._send_staff_log(message, decision, escalated=True)
                return

            await self._execute_action(message, decision)

            await add_mod_log(
                session,
                user_id=message.author.id,
                action=decision["action"],
                reason=decision["reason"],
                confidence=decision["confidence"],
                message_content=message.content,
                channel_id=message.channel.id,
                mod_override=False,
            )
            await self._send_staff_log(message, decision, escalated=False)

    def _is_suspicious(self, content: str) -> bool:
        text = (content or "").lower()
        if profanity.contains_profanity(text):
            return True
        return any(w in text for w in self._custom_flagged_words)

    async def _execute_action(self, message: discord.Message, decision: dict) -> None:
        action = decision["action"]
        reason = decision["reason"]

        if action == "ignore":
            return

        if action == "warn":
            try:
                await message.author.send(f"⚠️ NEXUS Warning: {reason}")
            except discord.HTTPException:
                pass
            return

        if action == "mute":
            if self.settings.mute_role_id:
                role = message.guild.get_role(self.settings.mute_role_id)
                if role:
                    await message.author.add_roles(role, reason=f"NEXUS mute: {reason}")

                    duration = int(decision.get("duration_minutes", 0) or 0)
                    if duration > 0:
                        until = datetime.utcnow() + timedelta(minutes=duration)
                        if message.author.guild_permissions.moderate_members is False:
                            try:
                                await message.author.timeout(until, reason=f"NEXUS timed mute: {reason}")
                            except discord.HTTPException:
                                pass
            return

        if action == "kick":
            await message.author.kick(reason=f"NEXUS kick: {reason}")
            return

        if action == "ban":
            await message.author.ban(reason=f"NEXUS ban: {reason}", delete_message_days=1)

    async def _send_staff_log(self, message: discord.Message, decision: dict, escalated: bool) -> None:
        channel_id = self.settings.staff_log_channel_id
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            logger.warning("moderation.staff_channel_missing", channel_id=channel_id)
            return

        title = "NEXUS Moderation Escalation" if escalated else "NEXUS Moderation Action"
        embed = discord.Embed(
            title=title,
            color=discord.Color.orange() if escalated else discord.Color.red(),
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="User", value=f"{message.author} (`{message.author.id}`)", inline=False)
        embed.add_field(name="Channel", value=f"<#{message.channel.id}>", inline=True)
        embed.add_field(name="Action", value=decision["action"], inline=True)
        embed.add_field(name="Confidence", value=str(decision["confidence"]), inline=True)
        embed.add_field(name="Reason", value=decision["reason"][:1024], inline=False)
        embed.add_field(name="Message", value=(message.content or "(empty)")[:1024], inline=False)
        embed.set_footer(text="React ✅ approve / ❌ override")

        sent = await channel.send(embed=embed)
        await sent.add_reaction("✅")
        await sent.add_reaction("❌")
