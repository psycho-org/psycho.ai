import pytest
from unittest.mock import Mock
from datetime import datetime, timezone
from typing import Any
import discord

from bot.commands.highlights import (
    compute_highlight_score,
    get_top_highlights,
    create_highlights_embed,
    HighlightResult,
)


class TestComputeHighlightScore:
    @pytest.mark.asyncio
    async def test_no_reactions_returns_zero(self):
        mock_message = Mock(spec=discord.Message)
        mock_message.reactions = []

        score = await compute_highlight_score(mock_message)

        assert score == 0

    @pytest.mark.asyncio
    async def test_single_unique_reactor(self):
        mock_author = Mock(id=100)
        mock_reactor = Mock(id=200, bot=False)

        mock_reaction = Mock()
        mock_reaction.users = Mock(return_value=AsyncIterator([mock_reactor]))

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.reactions = [mock_reaction]

        score = await compute_highlight_score(mock_message)

        assert score == 1

    @pytest.mark.asyncio
    async def test_dedupe_same_user_across_multiple_emojis(self):
        mock_author = Mock(id=100)
        mock_reactor = Mock(id=200, bot=False)

        mock_reaction1 = Mock()
        mock_reaction1.users = Mock(return_value=AsyncIterator([mock_reactor]))

        mock_reaction2 = Mock()
        mock_reaction2.users = Mock(return_value=AsyncIterator([mock_reactor]))

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.reactions = [mock_reaction1, mock_reaction2]

        score = await compute_highlight_score(mock_message)

        assert score == 1

    @pytest.mark.asyncio
    async def test_exclude_bot_reactors(self):
        mock_author = Mock(id=100)
        mock_bot_reactor = Mock(id=200, bot=True)

        mock_reaction = Mock()
        mock_reaction.users = Mock(return_value=AsyncIterator([mock_bot_reactor]))

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.reactions = [mock_reaction]

        score = await compute_highlight_score(mock_message)

        assert score == 0

    @pytest.mark.asyncio
    async def test_exclude_author_self_reaction(self):
        mock_author = Mock(id=100)

        mock_reaction = Mock()
        mock_reaction.users = Mock(return_value=AsyncIterator([mock_author]))

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.reactions = [mock_reaction]

        score = await compute_highlight_score(mock_message)

        assert score == 0

    @pytest.mark.asyncio
    async def test_multiple_unique_human_reactors(self):
        mock_author = Mock(id=100)
        mock_reactor1 = Mock(id=200, bot=False)
        mock_reactor2 = Mock(id=300, bot=False)
        mock_reactor3 = Mock(id=400, bot=False)

        mock_reaction = Mock()
        mock_reaction.users = Mock(
            return_value=AsyncIterator([mock_reactor1, mock_reactor2, mock_reactor3])
        )

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.reactions = [mock_reaction]

        score = await compute_highlight_score(mock_message)

        assert score == 3

    @pytest.mark.asyncio
    async def test_mixed_reactors_filters_correctly(self):
        mock_author = Mock(id=100, bot=False)
        mock_human = Mock(id=200, bot=False)
        mock_bot = Mock(id=300, bot=True)

        mock_reaction = Mock()
        mock_reaction.users = Mock(
            return_value=AsyncIterator([mock_author, mock_human, mock_bot])
        )

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.reactions = [mock_reaction]

        score = await compute_highlight_score(mock_message)

        assert score == 1


class TestGetTopHighlights:
    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self):
        result = await get_top_highlights([])

        assert result == []

    @pytest.mark.asyncio
    async def test_excludes_bot_authored_messages(self):
        mock_bot_author = Mock(id=100, bot=True)

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_bot_author
        mock_message.webhook_id = None
        mock_message.reactions = []

        result = await get_top_highlights([mock_message])

        assert result == []

    @pytest.mark.asyncio
    async def test_excludes_webhook_messages(self):
        mock_author = Mock(id=100, bot=False)

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.webhook_id = 12345
        mock_message.reactions = []

        result = await get_top_highlights([mock_message])

        assert result == []

    @pytest.mark.asyncio
    async def test_threshold_excludes_zero_score(self):
        mock_author = Mock(id=100, bot=False)

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.webhook_id = None
        mock_message.reactions = []

        result = await get_top_highlights([mock_message])

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_top_3_by_score(self):
        messages: list[discord.Message] = []
        for i, score in enumerate([5, 3, 8, 1, 6], start=1):
            mock_author = Mock(id=100, bot=False)
            reactors = [Mock(id=200 + j, bot=False) for j in range(score)]

            mock_reaction = Mock()
            mock_reaction.users = Mock(return_value=AsyncIterator(reactors))

            mock_message = Mock(spec=discord.Message)
            mock_message.author = mock_author
            mock_message.webhook_id = None
            mock_message.reactions = [mock_reaction]
            mock_message.created_at = datetime(2026, 1, 1, 12, i, tzinfo=timezone.utc)

            messages.append(mock_message)

        result = await get_top_highlights(messages, top_n=3)

        assert len(result) == 3
        assert result[0].score == 8
        assert result[1].score == 6
        assert result[2].score == 5

    @pytest.mark.asyncio
    async def test_tie_break_by_recency(self):
        messages: list[discord.Message] = []
        for _, minutes in enumerate([10, 20, 30], start=1):
            mock_author = Mock(id=100, bot=False)
            mock_reactor = Mock(id=200, bot=False)

            mock_reaction = Mock()
            mock_reaction.users = Mock(return_value=AsyncIterator([mock_reactor]))

            mock_message = Mock(spec=discord.Message)
            mock_message.author = mock_author
            mock_message.webhook_id = None
            mock_message.reactions = [mock_reaction]
            mock_message.created_at = datetime(
                2026, 1, 1, 12, minutes, tzinfo=timezone.utc
            )

            messages.append(mock_message)

        result = await get_top_highlights(messages, top_n=3)

        assert len(result) == 3
        assert result[0].message.created_at.minute == 30
        assert result[1].message.created_at.minute == 20
        assert result[2].message.created_at.minute == 10


class TestCreateHighlightsEmbed:
    def test_empty_highlights_returns_friendly_message(self):
        embed = create_highlights_embed([], "test-channel")
        description = embed.description
        footer = embed.footer.text

        assert description is not None
        assert footer is not None

        assert "No highlights found" in description
        assert "test-channel" in footer

    def test_single_highlight_formatting(self):
        mock_author = Mock()
        mock_author.display_name = "TestUser"
        mock_author.name = "testuser"

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.jump_url = "https://discord.com/channels/123/456/789"

        highlight = HighlightResult(message=mock_message, score=1)

        embed = create_highlights_embed([highlight], "test-channel")
        description = embed.description or ""

        assert "🥇" in description
        assert "1 reaction" in description
        assert "TestUser" in description
        assert "https://discord.com/channels/123/456/789" in description

    def test_multiple_reactions_plural(self):
        mock_author = Mock()
        mock_author.display_name = "TestUser"
        mock_author.name = "testuser"

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.jump_url = "https://discord.com/channels/123/456/789"

        highlight = HighlightResult(message=mock_message, score=5)

        embed = create_highlights_embed([highlight], "test-channel")
        description = embed.description

        assert description is not None

        assert "5 reactions" in description

    def test_no_message_content_in_embed(self):
        mock_author = Mock()
        mock_author.display_name = "TestUser"
        mock_author.name = "testuser"

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.jump_url = "https://discord.com/channels/123/456/789"
        mock_message.content = "SECRET_CONTENT_SHOULD_NOT_APPEAR"

        highlight = HighlightResult(message=mock_message, score=1)

        embed = create_highlights_embed([highlight], "test-channel")
        description = embed.description or ""

        assert "SECRET_CONTENT_SHOULD_NOT_APPEAR" not in description

    def test_escapes_everyone_mentions(self):
        mock_author = Mock()
        mock_author.display_name = "@everyone"
        mock_author.name = "troll"

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.jump_url = "https://discord.com/channels/123/456/789"

        highlight = HighlightResult(message=mock_message, score=1)

        embed = create_highlights_embed([highlight], "test-channel")
        description = embed.description

        assert description is not None

        assert "@everyone" not in description
        assert "@\u200beveryone" in description

    def test_escapes_here_mentions(self):
        mock_author = Mock()
        mock_author.display_name = "@here"
        mock_author.name = "troll"

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.jump_url = "https://discord.com/channels/123/456/789"

        highlight = HighlightResult(message=mock_message, score=1)

        embed = create_highlights_embed([highlight], "test-channel")
        description = embed.description

        assert description is not None

        assert "@here" not in description
        assert "@\u200bhere" in description

    def test_escapes_user_mention_patterns(self):
        mock_author = Mock()
        mock_author.display_name = "<@123456789>"
        mock_author.name = "mention_troll"

        mock_message = Mock(spec=discord.Message)
        mock_message.author = mock_author
        mock_message.jump_url = "https://discord.com/channels/123/456/789"

        highlight = HighlightResult(message=mock_message, score=1)

        embed = create_highlights_embed([highlight], "test-channel")
        description = embed.description

        assert description is not None

        assert "<@123456789>" not in description
        assert "<\u200b@123456789>" in description

    def test_top_3_medals(self):
        highlights: list[HighlightResult] = []
        for i in range(3):
            mock_author = Mock()
            mock_author.display_name = f"User{i}"
            mock_author.name = f"user{i}"

            mock_message = Mock(spec=discord.Message)
            mock_message.author = mock_author
            mock_message.jump_url = f"https://discord.com/channels/123/456/{i}"

            highlights.append(HighlightResult(message=mock_message, score=3 - i))

        embed = create_highlights_embed(highlights, "test-channel")
        description = embed.description

        assert description is not None

        assert "🥇" in description
        assert "🥈" in description
        assert "🥉" in description


class AsyncIterator:
    def __init__(self, items: list[Any]):
        self.items: list[Any] = items
        self.index: int = 0

    def __aiter__(self) -> "AsyncIterator":
        return self

    async def __anext__(self) -> Any:
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item
        return item
