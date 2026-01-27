"""Summary cog - AI-powered conversation summarization"""

from discord.ext import commands


class SummaryCog(commands.Cog):
    """Cog for summarizing Discord conversations using AI"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Command implementations will be added in next task


async def setup(bot: commands.Bot) -> None:
    """Load the Summary cog"""
    await bot.add_cog(SummaryCog(bot))
