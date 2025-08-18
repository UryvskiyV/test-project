"""Tests for bot functionality."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram.types import Message, User

from src.bot.handlers import handle_help, handle_reset, handle_start, handle_user_message


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
    message.chat = Mock()
    message.chat.id = 123
    message.bot = Mock()
    message.bot.send_chat_action = AsyncMock()
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
        assert "v0.3.0" in call_args

    @pytest.mark.asyncio
    @patch("src.bot.handlers.save_user_interaction")
    @patch("src.bot.handlers.get_context_summary")
    @patch("src.bot.handlers.get_optimized_context_for_llm")
    @patch("src.bot.handlers.send_to_llm")
    async def test_handle_user_message_success(
        self,
        mock_send_to_llm: Mock,
        mock_get_context: Mock,
        mock_get_summary: Mock,
        mock_save_interaction: Mock,
        mock_message: Mock,
    ) -> None:
        """Test successful user message handling with context and LLM."""
        mock_message.text = "Hello, how are you?"
        mock_user = Mock()
        mock_user.id = 123456789
        mock_message.from_user = mock_user
        
        mock_get_context.return_value = [{"role": "user", "content": "Previous message"}]
        mock_send_to_llm.return_value = "I'm doing well, thank you for asking!"
        mock_get_summary.return_value = {"total_messages": 3}

        await handle_user_message(mock_message)

        # Check that context was retrieved
        mock_get_context.assert_called_once_with("123456789")

        # Check that LLM was called with context
        mock_send_to_llm.assert_called_once_with(
            "Hello, how are you?", 
            history=[{"role": "user", "content": "Previous message"}]
        )

        # Check that interaction was saved
        mock_save_interaction.assert_called_once_with(
            "123456789", "Hello, how are you?", "I'm doing well, thank you for asking!"
        )

        # Check that typing action was sent
        mock_message.bot.send_chat_action.assert_called_once_with(
            chat_id=123, action="typing"
        )

        # Check that answer was called with LLM response
        mock_message.answer.assert_called_once_with("I'm doing well, thank you for asking!")

    @pytest.mark.asyncio
    async def test_handle_user_message_empty_text(self, mock_message: Mock) -> None:
        """Test user message handler with empty text."""
        mock_message.text = None

        await handle_user_message(mock_message)

        # Check that appropriate error message was sent
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "текстовыми сообщениями" in call_args

    @pytest.mark.asyncio
    @patch("src.bot.handlers.send_to_llm")
    async def test_handle_user_message_llm_error(self, mock_send_to_llm: Mock, mock_message: Mock) -> None:
        """Test user message handling with LLM error."""
        from src.llm.service import LLMError

        mock_message.text = "Hello"
        mock_send_to_llm.side_effect = LLMError("API unavailable")

        await handle_user_message(mock_message)

        # Check that error message was sent
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "произошла ошибка" in call_args

    @pytest.mark.asyncio
    @patch("src.bot.handlers.reset_user_context")
    @patch("src.bot.handlers.get_context_summary")
    async def test_handle_reset_success(
        self, mock_get_summary: Mock, mock_reset_context: Mock, mock_message: Mock
    ) -> None:
        """Test successful reset command handling."""
        mock_user = Mock()
        mock_user.id = 123456789
        mock_message.from_user = mock_user
        mock_get_summary.return_value = {
            "total_messages": 5,
            "estimated_tokens": 150,
        }

        await handle_reset(mock_message)

        # Check that summary was retrieved
        mock_get_summary.assert_called_once_with("123456789")

        # Check that context was reset
        mock_reset_context.assert_called_once_with("123456789")

        # Check that confirmation message was sent
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Контекст диалога сброшен" in call_args
        assert "5" in call_args  # Message count
        assert "150" in call_args  # Token count

    @pytest.mark.asyncio
    @patch("src.bot.handlers.get_context_summary")
    async def test_handle_reset_error(self, mock_get_summary: Mock, mock_message: Mock) -> None:
        """Test reset command with error."""
        mock_user = Mock()
        mock_user.id = 123456789
        mock_message.from_user = mock_user
        mock_get_summary.side_effect = Exception("Storage error")

        await handle_reset(mock_message)

        # Check that error message was sent
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "ошибка при сбросе контекста" in call_args
