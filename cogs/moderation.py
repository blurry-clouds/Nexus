from discord.ext import commands


class ModerationCog(commands.Cog):
    """Step-1 scaffold for moderation pipeline.

    Future steps implement:
    on_message -> local pre-screen -> Claude decision -> action executor.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
