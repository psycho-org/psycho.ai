"""Permission checking utilities for Discord commands"""

from typing import List

import discord


def has_allowed_role(
        interaction: discord.Interaction, allowed_role_ids: List[int]
) -> bool:
    """
    Check if the user invoking the interaction has any of the allowed roles.

    Args:
        interaction: Discord interaction from a slash command
        allowed_role_ids: List of role IDs that are allowed to use the command

    Returns:
        True if user has permission (has allowed role or no restrictions configured),
        False otherwise

    Note:
        If allowed_role_ids is empty, all users are allowed (no restrictions).
    """
    # No restrictions if no roles configured
    if not allowed_role_ids:
        return True

    # Interaction must be in a guild to check roles
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return False

    # Check if user has any of the allowed roles
    member_role_ids = {role.id for role in interaction.user.roles}
    return bool(member_role_ids & set(allowed_role_ids))


def get_permission_error_message(allowed_role_ids: List[int]) -> str:
    """
    Generate a helpful error message when permission is denied.

    Args:
        allowed_role_ids: List of role IDs that are allowed

    Returns:
        Formatted error message explaining the permission requirement
    """
    if not allowed_role_ids:
        return "You do not have permission to use this command."

    role_mentions = " or ".join(f"<@&{role_id}>" for role_id in allowed_role_ids)
    return f"You need one of these roles to use this command: {role_mentions}"
