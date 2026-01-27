"""Web search cog - AI-powered web search with summarization"""

from discord.ext import commands


class WebSearchCog(commands.Cog):
    """Cog for web search with AI-powered summarization"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Command implementations will be added in next task


async def setup(bot: commands.Bot) -> None:
    """Load the WebSearch cog"""
    await bot.add_cog(WebSearchCog(bot))
