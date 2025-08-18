"""Tests for bot resilience and error handling."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from openai import APIError, RateLimitError, APIConnectionError, APITimeoutError

from src.llm.service import (
    LLMError,
    LLMRateLimitError, 
    LLMTimeoutError,
    LLMConnectionError,
    send_to_llm,
    _make_llm_request_with_retry,
    _is_retryable_api_error,
)
from src.llm.prompts import create_adaptive_system_prompt, _contains_keywords
from src.dialog.manager import get_optimized_context_for_llm


class TestErrorHandling:
    """Test cases for API error handling."""

    @pytest.mark.asyncio
    @patch("src.llm.service.create_openrouter_client")
    async def test_rate_limit_error_handling(self, mock_create_client: Mock) -> None:
        """Test rate limit error handling with proper retry logic."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Simulate rate limit error
        rate_limit_error = RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(),
            body={}
        )
        mock_client.chat.completions.create.side_effect = rate_limit_error
        
        with pytest.raises(LLMRateLimitError, match="API rate limit exceeded"):
            send_to_llm("test message", client=mock_client)

    @pytest.mark.asyncio  
    @patch("src.llm.service.create_openrouter_client")
    async def test_timeout_error_handling(self, mock_create_client: Mock) -> None:
        """Test timeout error handling."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Simulate timeout error
        timeout_error = APITimeoutError(request=MagicMock())
        mock_client.chat.completions.create.side_effect = timeout_error
        
        with pytest.raises(LLMTimeoutError, match="API request timed out"):
            send_to_llm("test message", client=mock_client)

    @pytest.mark.asyncio
    @patch("src.llm.service.create_openrouter_client") 
    async def test_connection_error_handling(self, mock_create_client: Mock) -> None:
        """Test connection error handling."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Simulate connection error
        connection_error = APIConnectionError(request=MagicMock())
        mock_client.chat.completions.create.side_effect = connection_error
        
        with pytest.raises(LLMConnectionError, match="API connection failed"):
            send_to_llm("test message", client=mock_client)

    @patch("src.llm.service.time.sleep")
    def test_retry_with_exponential_backoff(self, mock_sleep: Mock) -> None:
        """Test retry logic with exponential backoff."""
        mock_client = Mock()
        
        # First 2 attempts fail, 3rd succeeds
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Success"
        
        mock_client.chat.completions.create.side_effect = [
            APIConnectionError(request=MagicMock()),
            APIConnectionError(request=MagicMock()),
            mock_response
        ]
        
        messages = [{"role": "user", "content": "test"}]
        config = {"model": "test-model"}
        
        result = _make_llm_request_with_retry(mock_client, messages, config)
        
        assert result == mock_response
        assert mock_sleep.call_count == 2  # 2 retries before success
        mock_sleep.assert_any_call(1)  # First retry: 2^0 = 1
        mock_sleep.assert_any_call(2)  # Second retry: 2^1 = 2

    def test_is_retryable_api_error(self) -> None:
        """Test retryable error detection."""
        # Test retryable status codes
        retryable_error = Mock(spec=APIError)
        retryable_error.status_code = 503
        assert _is_retryable_api_error(retryable_error) is True
        
        # Test non-retryable status code
        non_retryable_error = Mock(spec=APIError)
        non_retryable_error.status_code = 400
        non_retryable_error.__str__ = lambda self: "Bad request"
        assert _is_retryable_api_error(non_retryable_error) is False
        
        # Test retryable error message
        timeout_error = Mock(spec=APIError)
        timeout_error.status_code = 200
        timeout_error.__str__ = lambda self: "timeout occurred"
        assert _is_retryable_api_error(timeout_error) is True


class TestAdaptivePrompts:
    """Test cases for adaptive system prompts."""

    def test_default_prompt_without_history(self) -> None:
        """Test default prompt when no history provided."""
        prompt = create_adaptive_system_prompt()
        assert "умный и полезный ИИ-помощник" in prompt
        assert "ОСНОВНЫЕ ПРИНЦИПЫ" in prompt

    def test_technical_context_prompt(self) -> None:
        """Test adaptive prompt for technical discussions."""
        history = [
            {"role": "user", "content": "Как написать Python код для API?"},
            {"role": "assistant", "content": "Вот пример кода..."},
            {"role": "user", "content": "А что насчет обработки ошибок в коде?"}
        ]
        
        prompt = create_adaptive_system_prompt(history)
        assert "ТЕКУЩИЙ КОНТЕКСТ: Техническое обсуждение" in prompt
        assert "детальные технические решения" in prompt

    def test_learning_context_prompt(self) -> None:
        """Test adaptive prompt for educational discussions."""
        history = [
            {"role": "user", "content": "Объясни как работает машинное обучение"},
            {"role": "assistant", "content": "Машинное обучение это..."},
            {"role": "user", "content": "Что такое нейронные сети?"}
        ]
        
        prompt = create_adaptive_system_prompt(history)
        assert "ТЕКУЩИЙ КОНТЕКСТ: Обучающий диалог" in prompt
        assert "пошаговые объяснения" in prompt

    def test_problem_solving_context_prompt(self) -> None:
        """Test adaptive prompt for problem-solving discussions."""
        history = [
            {"role": "user", "content": "У меня проблема с ботом"},
            {"role": "assistant", "content": "Давайте разберемся..."},
            {"role": "user", "content": "Помоги исправить эту ошибку"}
        ]
        
        prompt = create_adaptive_system_prompt(history)
        assert "ТЕКУЩИЙ КОНТЕКСТ: Решение проблемы" in prompt
        assert "конкретные шаги решения" in prompt

    def test_long_conversation_context_prompt(self) -> None:
        """Test adaptive prompt for long conversations."""
        # Create long history (>10 messages)
        history = []
        for i in range(12):
            history.append({"role": "user", "content": f"Message {i}"})
            
        prompt = create_adaptive_system_prompt(history)
        assert "КОНТЕКСТ: Длинный диалог" in prompt
        assert "избегай повторений" in prompt

    def test_contains_keywords_function(self) -> None:
        """Test keyword detection in conversation history."""
        history = [
            {"role": "user", "content": "Расскажи про Python программирование"},
            {"role": "assistant", "content": "Python это язык..."},
            {"role": "user", "content": "Как написать код?"}
        ]
        
        tech_keywords = ["python", "программ", "код"]
        assert _contains_keywords(history, tech_keywords) is True
        
        unrelated_keywords = ["погода", "еда", "спорт"]
        assert _contains_keywords(history, unrelated_keywords) is False

    def test_multiple_context_hints(self) -> None:
        """Test prompt with multiple context hints."""
        history = [
            {"role": "user", "content": "Объясни как исправить проблему с Python кодом"},
            {"role": "assistant", "content": "Давайте разберем код..."},
        ] * 6  # Make it long conversation too
        
        prompt = create_adaptive_system_prompt(history)
        assert "ТЕКУЩИЙ КОНТЕКСТ: Техническое обсуждение" in prompt
        assert "ТЕКУЩИЙ КОНТЕКСТ: Обучающий диалог" in prompt
        assert "ТЕКУЩИЙ КОНТЕКСТ: Решение проблемы" in prompt
        assert "КОНТЕКСТ: Длинный диалог" in prompt


class TestDialogManagerResilience:
    """Test cases for dialog manager resilience."""

    @patch("src.dialog.storage.clear_storage")
    def test_optimized_context_with_adaptive_prompt(self, mock_clear: Mock) -> None:
        """Test optimized context returns both history and adaptive prompt."""
        from src.dialog.storage import add_user_message, add_assistant_message
        
        user_id = "test_user_123"
        
        # Add some technical conversation
        add_user_message(user_id, "Как написать Python код?")
        add_assistant_message(user_id, "Вот пример Python кода...")
        add_user_message(user_id, "Объясни алгоритм сортировки")
        
        context, adaptive_prompt = get_optimized_context_for_llm(user_id)
        
        # Check that we get both context and adaptive prompt
        assert isinstance(context, list)
        assert isinstance(adaptive_prompt, str)
        assert len(context) > 0
        assert "ТЕКУЩИЙ КОНТЕКСТ: Техническое обсуждение" in adaptive_prompt

    def test_context_resilience_with_empty_history(self) -> None:
        """Test context handling with empty history."""
        user_id = "empty_user_123"
        
        context, adaptive_prompt = get_optimized_context_for_llm(user_id)
        
        # Should handle empty history gracefully
        assert isinstance(context, list)
        assert isinstance(adaptive_prompt, str)
        assert len(context) == 0  # No messages yet
        assert "умный и полезный ИИ-помощник" in adaptive_prompt


class TestBotErrorMessages:
    """Test cases for user-friendly error messages in bot handlers."""

    @pytest.mark.asyncio
    @patch("src.bot.handlers.get_optimized_context_for_llm")
    @patch("src.bot.handlers.send_to_llm")
    async def test_rate_limit_error_user_message(self, mock_send_to_llm: Mock, mock_get_context: Mock) -> None:
        """Test user-friendly message for rate limit errors."""
        from src.bot.handlers import handle_user_message
        
        # Setup mocks
        mock_get_context.return_value = ([], "test prompt")
        mock_send_to_llm.side_effect = LLMRateLimitError("Rate limit exceeded")
        
        # Mock message with proper async mocks
        mock_message = Mock()
        mock_message.text = "Test message"
        mock_user = Mock()
        mock_user.id = 123456789
        mock_message.from_user = mock_user
        mock_message.chat.id = 123
        
        # Create async mock for send_chat_action
        async def mock_send_action(*args, **kwargs):
            pass
        mock_message.bot.send_chat_action = mock_send_action
        
        # Create async mock for answer
        async def mock_answer(text):
            return Mock()
        mock_message.answer = Mock(side_effect=mock_answer)
        
        await handle_user_message(mock_message)
        
        # Check user-friendly error message
        mock_message.answer.assert_called_once()
        error_msg = mock_message.answer.call_args[0][0]
        assert "перегружен" in error_msg
        assert "подождите" in error_msg

    @pytest.mark.asyncio
    @patch("src.bot.handlers.get_optimized_context_for_llm")
    @patch("src.bot.handlers.send_to_llm")
    async def test_timeout_error_user_message(self, mock_send_to_llm: Mock, mock_get_context: Mock) -> None:
        """Test user-friendly message for timeout errors."""
        from src.bot.handlers import handle_user_message
        
        # Setup mocks
        mock_get_context.return_value = ([], "test prompt")
        mock_send_to_llm.side_effect = LLMTimeoutError("Request timed out")
        
        # Mock message with proper async mocks
        mock_message = Mock()
        mock_message.text = "Test message"
        mock_user = Mock()
        mock_user.id = 123456789
        mock_message.from_user = mock_user
        mock_message.chat.id = 123
        
        # Create async mock for send_chat_action
        async def mock_send_action(*args, **kwargs):
            pass
        mock_message.bot.send_chat_action = mock_send_action
        
        # Create async mock for answer
        async def mock_answer(text):
            return Mock()
        mock_message.answer = Mock(side_effect=mock_answer)
        
        await handle_user_message(mock_message)
        
        # Check user-friendly error message
        mock_message.answer.assert_called_once()
        error_msg = mock_message.answer.call_args[0][0]
        assert "время ожидания" in error_msg.lower()
        assert "попробуйте" in error_msg.lower()
