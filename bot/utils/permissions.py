"""Permission checking utilities for Discord commands"""

import discord
from typing import List


def has_allowed_role(member: discord.Member, allowed_role_ids: List[int]) -> bool:
    """Check if member has any of the allowed roles"""
    if not allowed_role_ids:
        return True  # No restrictions if no roles configured

    member_role_ids = {role.id for role in member.roles}
    return bool(member_role_ids & set(allowed_role_ids))
