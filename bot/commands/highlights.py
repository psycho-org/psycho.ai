"""Highlights commands - reaction-based message highlights"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging

import discord
from discord import app_commands

from bot.config import Config
from bot.utils.permissions import has_allowed_role, get_permission_error_message

logger = logging.getLogger(__name__)


@dataclass
class HighlightResult:
    message: discord.Message
    score: int


async def compute_highlight_score(message: discord.Message) -> int:
    """
    Compute highlight score for a message based on unique human reactors.

    Score = count of unique human reactors (deduplicated across all emojis)
    Excludes:
    - Bot reactors (user.bot == True)
    - Author self-reactions (reactor_id == author_id)

    Args:
        message: Discord message to score

    Returns:
        Score (0 or higher)
    """
    if not message.reactions:
        return 0

    unique_reactors: set[int] = set()
    author_id = message.author.id

    for reaction in message.reactions:
        try:
            async for user in reaction.users(limit=None):
                if not user.bot and user.id != author_id:
                    unique_reactors.add(user.id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            continue

    return len(unique_reactors)


async def get_top_highlights(
    messages: list[discord.Message], top_n: int = 3
) -> list[HighlightResult]:
    """
    Get top N highlighted messages from a list.

    Scoring:
    - Primary sort: score descending
    - Tie-break: message recency descending (created_at)
    - Threshold: score >= 1 (at least one non-author human reactor)

    Args:
        messages: List of Discord messages to analyze
        top_n: Number of top results to return (default: 3)

    Returns:
        List of HighlightResult objects (up to top_n items)
    """
    candidates = [
        msg for msg in messages if not msg.author.bot and msg.webhook_id is None
    ]

    results: list[HighlightResult] = []
    for msg in candidates:
        score = await compute_highlight_score(msg)
        if score >= 1:
            results.append(HighlightResult(message=msg, score=score))

    results.sort(key=lambda r: (r.score, r.message.created_at), reverse=True)

    return results[:top_n]


def create_highlights_embed(
    highlights: list[HighlightResult], channel_name: str
) -> discord.Embed:
    """
    Create embed for highlights results.

    Privacy-preserving: Shows only metadata (score, author, jump link).
    Does NOT include message content, attachments, or embeds.

    Args:
        highlights: List of HighlightResult objects
        channel_name: Name of the channel

    Returns:
        Discord Embed
    """
    if not highlights:
        embed = discord.Embed(
            title="📊 Highlights (Last 24 Hours)",
            description="No highlights found in the last 24 hours.",
            color=discord.Color.blue(),
        )
        _ = embed.set_footer(text=f"Channel: {channel_name}")
        return embed

    description_lines: list[str] = []
    for i, result in enumerate(highlights, 1):
        display_name = result.message.author.display_name or result.message.author.name
        safe_name = (
            display_name.replace("@everyone", "@\u200beveryone")
            .replace("@here", "@\u200bhere")
            .replace("<@", "<\u200b@")
        )

        medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
        reaction_text = "reaction" if result.score == 1 else "reactions"

        line = (
            f"{medal} **{result.score} {reaction_text}** • "
            f"Author: {safe_name} • "
            f"[Jump to message]({result.message.jump_url})"
        )
        description_lines.append(line)

    description = "\n\n".join(description_lines)

    embed = discord.Embed(
        title="📊 Highlights (Last 24 Hours)",
        description=description,
        color=discord.Color.gold(),
    )

    _ = embed.set_footer(
        text=f"Channel: {channel_name} • Top {len(highlights)} messages"
    )

    return embed


def register_highlights_commands(
    tree: app_commands.CommandTree, config: Config
) -> None:
    """Register highlights commands to the command tree"""

    @tree.command(
        name="highlights",
        description="Show top 3 most-reacted messages from last 24 hours",
    )
    async def highlights(interaction: discord.Interaction):
        if not has_allowed_role(interaction, config.allowed_role_ids):
            error_msg = get_permission_error_message(config.allowed_role_ids)
            _ = await interaction.response.send_message(error_msg, ephemeral=True)
            return

        try:
            if not interaction.response.is_done():
                _ = await interaction.response.defer()
        except discord.NotFound:
            return

        try:
            if not isinstance(
                interaction.channel, (discord.TextChannel, discord.Thread)
            ):
                _ = await interaction.followup.send(
                    "This command only works in text channels and threads.",
                    ephemeral=True,
                )
                return

            channel = interaction.channel

            after_time = datetime.now(timezone.utc) - timedelta(hours=24)
            messages: list[discord.Message] = []

            async for message in channel.history(
                limit=config.message_limit, after=after_time, oldest_first=False
            ):
                messages.append(message)

            if not messages:
                channel_name = channel.name if hasattr(channel, "name") else "Unknown"
                embed = create_highlights_embed([], channel_name)
                _ = await interaction.followup.send(
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                return

            top_highlights = await get_top_highlights(messages, top_n=3)

            channel_name = channel.name if hasattr(channel, "name") else "Unknown"
            embed = create_highlights_embed(top_highlights, channel_name)

            _ = await interaction.followup.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )

        except discord.Forbidden:
            _ = await interaction.followup.send(
                "I don't have permission to read message history in this channel.",
                ephemeral=True,
            )
        except Exception:
            logger.exception("Unexpected error while fetching highlights")
            _ = await interaction.followup.send(
                "An error occurred while fetching highlights.", ephemeral=True
            )

    _ = highlights
