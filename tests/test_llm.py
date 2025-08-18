"""Tests for LLM functionality."""

from unittest.mock import Mock, patch

import pytest
from openai.types.chat import ChatCompletion

from src.llm.client import (
    create_openrouter_client,
    get_llm_config,
    validate_openrouter_connection,
)
from src.llm.prompts import (
    create_assistant_message,
    create_prompt,
    create_system_message,
    create_user_message,
    validate_history,
    validate_message_format,
)
from src.llm.service import (
    LLMConnectionError,
    LLMValidationError,
    send_to_llm,
)


class TestLLMClient:
    """Test cases for LLM client functionality."""

    def test_get_llm_config(self) -> None:
        """Test LLM configuration retrieval."""
        config = get_llm_config()

        assert isinstance(config, dict)
        assert "model" in config
        assert "temperature" in config
        assert "max_tokens" in config
        assert "top_p" in config

        assert isinstance(config["temperature"], float)
        assert isinstance(config["max_tokens"], int)
        assert isinstance(config["top_p"], float)

    def test_create_openrouter_client_missing_key(self) -> None:
        """Test client creation with missing API key."""
        with patch("src.llm.client.OPENROUTER_API_KEY", "test_key"):
            with pytest.raises(ValueError, match="OpenRouter API key is required"):
                create_openrouter_client()

    @patch("src.llm.client.OpenAI")
    def test_validate_openrouter_connection_success(self, mock_openai: Mock) -> None:
        """Test successful OpenRouter connection validation."""
        # Mock response
        mock_response = Mock(spec=ChatCompletion)
        mock_response.choices = [Mock()]

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response

        result = validate_openrouter_connection(mock_client)
        assert result is True

    @patch("src.llm.client.OpenAI")
    def test_validate_openrouter_connection_failure(self, mock_openai: Mock) -> None:
        """Test failed OpenRouter connection validation."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Connection failed")

        result = validate_openrouter_connection(mock_client)
        assert result is False


class TestLLMPrompts:
    """Test cases for prompt functionality."""

    def test_create_system_message(self) -> None:
        """Test system message creation."""
        content = "You are a helpful assistant"
        message = create_system_message(content)

        assert message["role"] == "system"
        assert message["content"] == content

    def test_create_user_message(self) -> None:
        """Test user message creation."""
        content = "Hello, how are you?"
        message = create_user_message(content)

        assert message["role"] == "user"
        assert message["content"] == content

    def test_create_assistant_message(self) -> None:
        """Test assistant message creation."""
        content = "I'm doing well, thank you!"
        message = create_assistant_message(content)

        assert message["role"] == "assistant"
        assert message["content"] == content

    def test_create_prompt_simple(self) -> None:
        """Test simple prompt creation."""
        user_message = "Hello"
        messages = create_prompt(user_message)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == user_message

    def test_create_prompt_with_history(self) -> None:
        """Test prompt creation with conversation history."""
        user_message = "How are you?"
        history = [
            create_user_message("Hello"),
            create_assistant_message("Hi there!")
        ]

        messages = create_prompt(user_message, history)

        assert len(messages) == 4  # system + 2 history + current user message
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert messages[3]["role"] == "user"
        assert messages[3]["content"] == user_message

    def test_validate_message_format_valid(self) -> None:
        """Test message format validation with valid message."""
        valid_message = {"role": "user", "content": "Hello"}
        assert validate_message_format(valid_message) is True

    def test_validate_message_format_invalid(self) -> None:
        """Test message format validation with invalid messages."""
        invalid_messages = [
            {"role": "invalid_role", "content": "Hello"},
            {"role": "user"},  # Missing content
            {"content": "Hello"},  # Missing role
            {"role": "user", "content": ""},  # Empty content
            "not a dict",  # Not a dictionary
        ]

        for invalid_message in invalid_messages:
            assert validate_message_format(invalid_message) is False

    def test_validate_history_valid(self) -> None:
        """Test history validation with valid history."""
        valid_history = [
            create_user_message("Hello"),
            create_assistant_message("Hi!")
        ]
        assert validate_history(valid_history) is True

    def test_validate_history_invalid(self) -> None:
        """Test history validation with invalid history."""
        invalid_histories = [
            [{"role": "invalid", "content": "Hello"}],  # Invalid role
            [{"role": "user"}],  # Missing content
            "not a list",  # Not a list
            [{"role": "user", "content": "Hello"}, "invalid"],  # Mixed valid/invalid
        ]

        for invalid_history in invalid_histories:
            assert validate_history(invalid_history) is False


class TestLLMService:
    """Test cases for LLM service functionality."""

    def test_send_to_llm_empty_message(self) -> None:
        """Test sending empty message to LLM."""
        with pytest.raises(LLMValidationError, match="User message cannot be empty"):
            send_to_llm("")

    def test_send_to_llm_invalid_history(self) -> None:
        """Test sending message with invalid history."""
        invalid_history = [{"role": "invalid", "content": "test"}]

        with pytest.raises(LLMValidationError, match="Invalid history format"):
            send_to_llm("Hello", history=invalid_history)

    @patch("src.llm.service.create_openrouter_client")
    def test_send_to_llm_success(self, mock_create_client: Mock) -> None:
        """Test successful LLM request."""
        # Mock client and response
        mock_client = Mock()
        mock_create_client.return_value = mock_client

        # Create a proper mock response
        mock_message = Mock()
        mock_message.content = "Hello! How can I help you?"

        mock_choice = Mock()
        mock_choice.message = mock_message

        mock_response = Mock(spec=ChatCompletion)
        mock_response.choices = [mock_choice]

        mock_client.chat.completions.create.return_value = mock_response

        # Test the function
        result = send_to_llm("Hello")

        assert result == "Hello! How can I help you?"
        mock_client.chat.completions.create.assert_called_once()

    @patch("src.llm.service.create_openrouter_client")
    def test_send_to_llm_client_error(self, mock_create_client: Mock) -> None:
        """Test LLM request with client creation error."""
        mock_create_client.side_effect = Exception("API key invalid")

        with pytest.raises(LLMConnectionError, match="Failed to create LLM client"):
            send_to_llm("Hello")

    def test_send_to_llm_with_provided_client(self) -> None:
        """Test LLM request with provided client."""
        # Create mock client
        mock_client = Mock()

        # Create a proper mock response
        mock_message = Mock()
        mock_message.content = "Test response"

        mock_choice = Mock()
        mock_choice.message = mock_message

        mock_response = Mock(spec=ChatCompletion)
        mock_response.choices = [mock_choice]

        mock_client.chat.completions.create.return_value = mock_response

        # Test the function
        result = send_to_llm("Hello", client=mock_client)

        assert result == "Test response"
        mock_client.chat.completions.create.assert_called_once()
