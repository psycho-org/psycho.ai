"""Configuration management for Discord bot"""

import os
from typing import List


class Config:
    """Bot configuration loaded from environment variables"""

    # Discord settings
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    DISCORD_GUILD_ID: str = os.getenv("DISCORD_GUILD_ID", "")

    # AI server settings
    AI_SERVER_URL: str = os.getenv("AI_SERVER_URL", "")
    AI_TIMEOUT_SECONDS: int = int(os.getenv("AI_TIMEOUT_SECONDS", "60"))

    # Permission settings
    ALLOWED_ROLE_IDS: List[int] = [
        int(role_id.strip())
        for role_id in os.getenv("ALLOWED_ROLE_IDS", "").split(",")
        if role_id.strip()
    ]

    # Web search settings
    WEB_SEARCH_API_KEY: str = os.getenv("WEB_SEARCH_API_KEY", "")
    WEB_SEARCH_API_TYPE: str = os.getenv("WEB_SEARCH_API_TYPE", "brave")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is required")

        if not cls.AI_SERVER_URL:
            raise ValueError("AI_SERVER_URL is required")
