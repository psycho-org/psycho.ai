"""Configuration management for Discord bot"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    """Bot configuration loaded from environment variables with validation"""

    # Discord settings
    discord_token: str = field(default_factory=lambda: os.getenv("DISCORD_TOKEN", ""))
    discord_guild_id: str = field(
        default_factory=lambda: os.getenv("DISCORD_GUILD_ID", "")
    )

    # AI server settings
    ai_server_url: str = field(default_factory=lambda: os.getenv("AI_SERVER_URL", ""))
    ai_timeout: int = field(
        default_factory=lambda: int(os.getenv("AI_TIMEOUT_SECONDS", "60"))
    )

    # Message settings
    # Maximum number of messages to fetch from a channel when processing
    # (limits API calls and processing time for AI requests)
    message_limit: int = field(
        default_factory=lambda: int(os.getenv("MESSAGE_LIMIT", "500"))
    )

    # Permission settings
    allowed_role_ids: List[int] = field(
        default_factory=lambda: [
            int(role_id.strip())
            for role_id in os.getenv("ALLOWED_ROLE_IDS", "").split(",")
            if role_id.strip()
        ]
    )

    # Web search settings
    web_search_api_key: str = field(
        default_factory=lambda: os.getenv("WEB_SEARCH_API_KEY", "")
    )
    web_search_api_type: str = field(
        default_factory=lambda: os.getenv("WEB_SEARCH_API_TYPE", "brave")
    )

    def __post_init__(self) -> None:
        """Validate required configuration after initialization"""
        if not self.discord_token:
            raise ValueError(
                "DISCORD_TOKEN is required. Please set it in your .env file or environment variables."
            )

        if not self.ai_server_url:
            raise ValueError(
                "AI_SERVER_URL is required. Please set it in your .env file or environment variables."
            )

        # Validate timeout is positive
        if self.ai_timeout <= 0:
            raise ValueError(
                f"AI_TIMEOUT_SECONDS must be positive, got {self.ai_timeout}"
            )

        # Validate message limit is positive
        if self.message_limit <= 0:
            raise ValueError(
                f"MESSAGE_LIMIT must be positive, got {self.message_limit}"
            )
