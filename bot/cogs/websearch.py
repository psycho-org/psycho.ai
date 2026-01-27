"""Web search cog - AI-powered web search with summarization"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Any

from bot.services.web_search import create_client, WebSearchError
from bot.utils.permissions import has_allowed_role, get_permission_error_message


class WebSearchCog(commands.Cog):
    """Cog for web search with AI-powered summarization"""

    def __init__(self, bot: commands.Bot):
        self.bot: Any = bot  # Use Any to avoid LSP errors with custom bot.config

    @app_commands.command(
        name="web-search", description="Search the web and summarize results"
    )
    @app_commands.describe(query="Search query", num_results="Number of results (1-10)")
    async def web_search(
        self, interaction: discord.Interaction, query: str, num_results: int = 5
    ):
        # Defer response immediately (must be within 3 seconds)
        await interaction.response.defer()

        if not has_allowed_role(interaction, self.bot.config.allowed_role_ids):
            error_msg = get_permission_error_message(self.bot.config.allowed_role_ids)
            await interaction.followup.send(error_msg, ephemeral=True)
            return

        if num_results < 1 or num_results > 10:
            await interaction.followup.send(
                "Number of results must be between 1 and 10.", ephemeral=True
            )
            return

        try:
            async with create_client(
                self.bot.config.web_search_api_type, self.bot.config.web_search_api_key
            ) as client:
                results = await client.search(query, num_results)

            if not results:
                await interaction.followup.send(
                    f"No results found for query: **{query}**", ephemeral=True
                )
                return

            embed = discord.Embed(title=f"Search: {query}", color=discord.Color.blue())

            for i, result in enumerate(results, 1):
                # Truncate description if too long (field value max 1024 chars)
                description = result.description
                if len(description) > 200:
                    description = description[:197] + "..."

                field_value = f"{description}\n[View]({result.url})"

                # Truncate field value if still too long
                if len(field_value) > 1024:
                    field_value = field_value[:1021] + "..."

                embed.add_field(
                    name=f"{i}. {result.title}", value=field_value, inline=False
                )

            if results[0].thumbnail_url:
                embed.set_thumbnail(url=results[0].thumbnail_url)

            provider_name = self.bot.config.web_search_api_type.capitalize()
            embed.set_footer(text=f"Powered by {provider_name}")

            await interaction.followup.send(embed=embed)

        except WebSearchError as e:
            await interaction.followup.send(f"Web search failed: {e}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Unexpected error: {e}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Load the WebSearch cog"""
    await bot.add_cog(WebSearchCog(bot))
