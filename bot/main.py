"""Discord bot entry point for psycho.ai"""

import logging
import os
from typing import Optional

import discord
from discord.ext import commands

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Bot(commands.Bot):
    """Custom Discord bot for psycho.ai with AI-powered features"""

    def __init__(self):
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",  # Fallback prefix for text commands
            intents=intents,
            help_command=None,  # We'll use slash commands primarily
        )

        self.guild_id: Optional[int] = None
        if guild_id := os.getenv("DISCORD_GUILD_ID"):
            self.guild_id = int(guild_id)

    async def setup_hook(self) -> None:
        """Called when the bot is starting up. Load cogs and sync commands."""
        logger.info("Running setup hook...")

        # Load cogs
        cogs_to_load = [
            "bot.cogs.summary",
            "bot.cogs.websearch",
        ]

        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")

        # Sync commands to guild (faster) or globally
        if self.guild_id:
            guild = discord.Object(id=self.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Synced commands to guild {self.guild_id}")
        else:
            await self.tree.sync()
            logger.info("Synced commands globally")

    async def on_ready(self) -> None:
        """Called when the bot is ready and connected to Discord"""
        logger.info(f"Bot is ready! Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")

        if self.guild_id:
            logger.info(f"Configured for guild ID: {self.guild_id}")


def main():
    """Main entry point for the Discord bot"""
    token = os.getenv("DISCORD_TOKEN")

    if not token:
        logger.error("DISCORD_TOKEN environment variable not set")
        raise ValueError("DISCORD_TOKEN is required")

    bot = Bot()
    bot.run(token)


if __name__ == "__main__":
    main()
