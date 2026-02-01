"""Discord message history collection service"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import discord
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class TimeScope:
    """Fetch messages from the last N minutes"""

    minutes: int


@dataclass
class MessageLinkScope:
    """Fetch messages from a specific message ID onward"""

    message_id: int


HistoryScope = TimeScope | MessageLinkScope


async def collect_history(
    channel: discord.TextChannel, scope: HistoryScope, message_limit: int = 500
) -> list[discord.Message]:
    """
    Collect message history from a Discord channel based on scope.

    Args:
        channel: Discord text channel to fetch messages from
        scope: TimeScope or MessageLinkScope defining the fetch range
        message_limit: Maximum number of messages to fetch (default: 500)

    Returns:
        List of messages in chronological order (oldest first)

    Raises:
        ValueError: If message_id in MessageLinkScope is invalid
    """
    messages: list[discord.Message] = []

    # Determine the 'after' parameter based on scope type
    if isinstance(scope, TimeScope):
        # Calculate datetime for time-based scope
        after = datetime.now(timezone.utc) - timedelta(minutes=scope.minutes)

        # Fetch messages after the calculated time
        async for message in channel.history(
            limit=message_limit, after=after, oldest_first=True
        ):
            messages.append(message)

    elif isinstance(scope, MessageLinkScope):
        # Fetch the specific message to use as 'after' parameter
        try:
            target_message = await channel.fetch_message(scope.message_id)
        except discord.NotFound:
            raise ValueError(
                f"Message with ID {scope.message_id} not found in channel {channel.name}"
            )
        except discord.HTTPException as e:
            raise ValueError(f"Failed to fetch message {scope.message_id}: {e}")

        # Fetch messages after the target message
        async for message in channel.history(
            limit=message_limit, after=target_message, oldest_first=True
        ):
            messages.append(message)

    logger.info(f"Collected {len(messages)} messages")
    return messages
