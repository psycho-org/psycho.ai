"""Discord bot entry point for psycho.ai"""

import logging
from typing import Optional
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from bot.config import Config

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Bot(commands.Bot):
    """Custom Discord bot for psycho.ai with AI-powered features"""

    def __init__(self, config: Config):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

        self.config = config
        self.guild_id: Optional[int] = None
        if config.discord_guild_id:
            self.guild_id = int(config.discord_guild_id)

    async def setup_hook(self) -> None:
        logger.info("Running setup hook...")

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

        if self.guild_id:
            guild = discord.Object(id=self.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Synced commands to guild {self.guild_id}")
        else:
            await self.tree.sync()
            logger.info("Synced commands globally")

    async def on_ready(self) -> None:
        if self.user:
            logger.info(f"Bot is ready! Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")

        if self.guild_id:
            logger.info(f"Configured for guild ID: {self.guild_id}")


def main():
    try:
        config = Config()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise

    bot = Bot(config)
    bot.run(config.discord_token)


if __name__ == "__main__":
    main()
