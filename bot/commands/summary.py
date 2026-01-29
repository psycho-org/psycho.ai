"""Summary commands - AI-powered conversation summarization"""

import re
from typing import Optional

import discord
from discord import app_commands
from discord.app_commands import Choice

from bot.config import Config
from bot.services.ai_client import (
    AIClient,
    AITimeoutError,
    AIConnectionError,
    AIResponseError,
)
from bot.services.history_collector import (
    collect_history,
    TimeScope,
    MessageLinkScope,
    HistoryScope,
)
from bot.utils.permissions import has_allowed_role, get_permission_error_message


def _parse_scope(scope_type: str, scope_value: str) -> HistoryScope:
    """
    Parse scope option into TimeScope or MessageLinkScope.

    Args:
        scope_type: "time" or "link"
        scope_value: Time format (30m/1h/2h) or message link/ID

    Returns:
        TimeScope or MessageLinkScope

    Raises:
        ValueError: If scope format is invalid
    """
    if scope_type == "time":
        match = re.match(r"^(\d+)([mh])$", scope_value.lower().strip())
        if not match:
            raise ValueError(
                "Invalid time format. Use 30m, 1h, or 2h (e.g., '30m' for 30 minutes)"
            )

        amount, unit = match.groups()
        minutes = int(amount) if unit == "m" else int(amount) * 60

        return TimeScope(minutes=minutes)

    elif scope_type == "link":
        link_match = re.search(r"/(\d+)$", scope_value)
        if link_match:
            message_id = int(link_match.group(1))
        else:
            try:
                message_id = int(scope_value.strip())
            except ValueError:
                raise ValueError(
                    "Invalid message link or ID. Provide a Discord message link or numeric message ID"
                )

        return MessageLinkScope(message_id=message_id)

    else:
        raise ValueError(f"Invalid scope type: {scope_type}")


def _format_messages_for_ai(messages: list[discord.Message]) -> list[str]:
    """
    Convert Discord messages to string list for AI client.

    Args:
        messages: List of Discord messages

    Returns:
        List of formatted message strings
    """
    formatted = []
    for msg in messages:
        author_name = msg.author.display_name or msg.author.name
        formatted.append(f"{author_name}: {msg.content}")

    return formatted


def _create_embed(
    title: str,
    description: str,
    message_count: int,
    time_range: Optional[str] = None,
) -> discord.Embed:
    """
    Create a Discord Embed for command response.

    Args:
        title: Embed title
        description: Embed description (AI result)
        message_count: Number of messages processed
        time_range: Optional time range string

    Returns:
        Discord Embed
    """
    if len(description) > 4000:
        description = description[:3997] + "..."

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue(),
    )

    footer_text = f"Covering {message_count} messages"
    if time_range:
        footer_text += f" from {time_range}"

    embed.set_footer(text=footer_text)

    return embed


def register_summary_commands(tree: app_commands.CommandTree, config: Config) -> None:
    """Register summary commands to the command tree"""

    @tree.command(
        name="summarize", description="Summarize conversation in this channel"
    )
    @app_commands.describe(
        scope_type="How to determine scope",
        scope_value="Time (30m/1h/2h) or message link",
    )
    @app_commands.choices(
        scope_type=[
            Choice(name="Time-based", value="time"),
            Choice(name="From message link", value="link"),
        ]
    )
    async def summarize(
        interaction: discord.Interaction, scope_type: str, scope_value: str
    ):
        """Summarize conversation (public result)"""
        if not has_allowed_role(interaction, config.allowed_role_ids):
            error_msg = get_permission_error_message(config.allowed_role_ids)
            await interaction.response.send_message(error_msg, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            scope = _parse_scope(scope_type, scope_value)

            if not isinstance(interaction.channel, discord.TextChannel):
                await interaction.followup.send(
                    "This command can only be used in text channels.",
                    ephemeral=True,
                )
                return

            messages = await collect_history(
                interaction.channel, scope, config.message_limit
            )

            if not messages:
                await interaction.followup.send(
                    "No messages found in specified range.", ephemeral=True
                )
                return

            formatted_messages = _format_messages_for_ai(messages)

            async with AIClient(config.ai_server_url, config.ai_timeout) as client:
                result = await client.summarize(formatted_messages)

            embed = _create_embed(
                title="Conversation Summary",
                description=result.summary,
                message_count=result.message_count,
                time_range=result.time_range,
            )

            await interaction.followup.send(embed=embed)

        except ValueError as e:
            await interaction.followup.send(
                f"Invalid scope format: {e}", ephemeral=True
            )
        except AITimeoutError:
            await interaction.followup.send(
                "Request timed out. Please try again.", ephemeral=True
            )
        except (AIConnectionError, AIResponseError) as e:
            await interaction.followup.send(f"AI service error: {e}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Unexpected error: {e}", ephemeral=True)

    @tree.command(
        name="decision-template",
        description="Extract decisions from conversation as template",
    )
    @app_commands.describe(
        scope_type="How to determine scope",
        scope_value="Time (30m/1h/2h) or message link",
    )
    @app_commands.choices(
        scope_type=[
            Choice(name="Time-based", value="time"),
            Choice(name="From message link", value="link"),
        ]
    )
    async def decision_template(
        interaction: discord.Interaction, scope_type: str, scope_value: str
    ):
        """Extract decisions from conversation (public result)"""
        if not has_allowed_role(interaction, config.allowed_role_ids):
            error_msg = get_permission_error_message(config.allowed_role_ids)
            await interaction.response.send_message(error_msg, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            scope = _parse_scope(scope_type, scope_value)

            if not isinstance(interaction.channel, discord.TextChannel):
                await interaction.followup.send(
                    "This command can only be used in text channels.",
                    ephemeral=True,
                )
                return

            messages = await collect_history(
                interaction.channel, scope, config.message_limit
            )

            if not messages:
                await interaction.followup.send(
                    "No messages found in specified range.", ephemeral=True
                )
                return

            formatted_messages = _format_messages_for_ai(messages)

            async with AIClient(config.ai_server_url, config.ai_timeout) as client:
                result = await client.extract_decisions(formatted_messages)

            if not result.decisions:
                description = "No decisions found in the conversation."
            else:
                decision_texts = []
                for i, decision in enumerate(result.decisions, 1):
                    decision_text = (
                        f"**{i}. {decision.title}**\n"
                        f"Owner: {decision.owner}\n"
                        f"Deadline: {decision.deadline}\n"
                        f"Context: {decision.context}\n"
                    )
                    decision_texts.append(decision_text)

                description = "\n".join(decision_texts)

            embed = _create_embed(
                title="Decision Template",
                description=description,
                message_count=len(formatted_messages),
            )

            await interaction.followup.send(embed=embed)

        except ValueError as e:
            await interaction.followup.send(
                f"Invalid scope format: {e}", ephemeral=True
            )
        except AITimeoutError:
            await interaction.followup.send(
                "Request timed out. Please try again.", ephemeral=True
            )
        except (AIConnectionError, AIResponseError) as e:
            await interaction.followup.send(f"AI service error: {e}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Unexpected error: {e}", ephemeral=True)

    @tree.command(
        name="catch-up", description="Generate catch-up narrative for missed messages"
    )
    @app_commands.describe(
        scope_type="How to determine scope",
        scope_value="Time (30m/1h/2h) or message link",
    )
    @app_commands.choices(
        scope_type=[
            Choice(name="Time-based", value="time"),
            Choice(name="From message link", value="link"),
        ]
    )
    async def catch_up(
        interaction: discord.Interaction, scope_type: str, scope_value: str
    ):
        """Generate catch-up narrative (ephemeral result)"""
        if not has_allowed_role(interaction, config.allowed_role_ids):
            error_msg = get_permission_error_message(config.allowed_role_ids)
            await interaction.response.send_message(error_msg, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            scope = _parse_scope(scope_type, scope_value)

            if not isinstance(interaction.channel, discord.TextChannel):
                await interaction.followup.send(
                    "This command can only be used in text channels.",
                    ephemeral=True,
                )
                return

            messages = await collect_history(
                interaction.channel, scope, config.message_limit
            )

            if not messages:
                await interaction.followup.send(
                    "No messages found in specified range.", ephemeral=True
                )
                return

            formatted_messages = _format_messages_for_ai(messages)

            async with AIClient(config.ai_server_url, config.ai_timeout) as client:
                result = await client.generate_catchup(formatted_messages)

            description = f"{result.narrative}\n\n**Key Points:**\n"
            for point in result.key_points:
                description += f"• {point}\n"

            embed = _create_embed(
                title="Catch Up",
                description=description,
                message_count=len(formatted_messages),
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError as e:
            await interaction.followup.send(
                f"Invalid scope format: {e}", ephemeral=True
            )
        except AITimeoutError:
            await interaction.followup.send(
                "Request timed out. Please try again.", ephemeral=True
            )
        except (AIConnectionError, AIResponseError) as e:
            await interaction.followup.send(f"AI service error: {e}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Unexpected error: {e}", ephemeral=True)
