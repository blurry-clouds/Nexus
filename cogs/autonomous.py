from discord.ext import commands


class AutonomousCog(commands.Cog):
    """Step-1 scaffold for autonomous behaviors and scheduler hooks."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
