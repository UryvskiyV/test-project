"""Tests for bot functionality."""

from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import Message, User

from src.bot.handlers import handle_help, handle_start, handle_unknown_message


@pytest.fixture
def mock_user() -> User:
    """Create mock user for testing."""
    return User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
        language_code="en",
        is_premium=False,
        added_to_attachment_menu=False,
        can_join_groups=False,
        can_read_all_group_messages=False,
        supports_inline_queries=False,
    )


@pytest.fixture
def mock_message(mock_user: User) -> Mock:
    """Create mock message for testing."""
    message = Mock(spec=Message)
    message.from_user = mock_user
    message.text = "/start"
    message.answer = AsyncMock()
    return message


class TestBotHandlers:
    """Test cases for bot handlers."""

    @pytest.mark.asyncio
    async def test_handle_start(self, mock_message: Mock) -> None:
        """Test /start command handler."""
        await handle_start(mock_message)

        # Check that answer was called
        mock_message.answer.assert_called_once()

        # Check that welcome message contains expected text
        call_args = mock_message.answer.call_args[0][0]
        assert "Добро пожаловать!" in call_args
        assert "/start" in call_args
        assert "/help" in call_args

    @pytest.mark.asyncio
    async def test_handle_help(self, mock_message: Mock) -> None:
        """Test /help command handler."""
        await handle_help(mock_message)

        # Check that answer was called
        mock_message.answer.assert_called_once()

        # Check that help message contains expected text
        call_args = mock_message.answer.call_args[0][0]
        assert "Справка по боту" in call_args
        assert "/start" in call_args
        assert "/help" in call_args
        assert "v0.1.0" in call_args

    @pytest.mark.asyncio
    async def test_handle_unknown_message(self, mock_message: Mock) -> None:
        """Test handler for unknown messages."""
        mock_message.text = "Hello, bot!"

        await handle_unknown_message(mock_message)

        # Check that answer was called
        mock_message.answer.assert_called_once()

        # Check that response contains expected text
        call_args = mock_message.answer.call_args[0][0]
        assert "не умею обрабатывать" in call_args
        assert "/start" in call_args
        assert "/help" in call_args
