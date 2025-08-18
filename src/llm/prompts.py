"""Prompts module for LLM interactions."""

from typing import Any

from src.logging_config import get_logger

logger = get_logger(__name__)

# Default system prompt for the assistant
DEFAULT_SYSTEM_PROMPT = """Ты - полезный помощник в Telegram боте. Ты отвечаешь на вопросы пользователей на русском языке, даешь полезные советы и помогаешь решать различные задачи.

Правила поведения:
- Отвечай кратко и по существу
- Используй дружелюбный тон
- Если не знаешь ответ, честно скажи об этом
- Не придумывай факты
- Помогай пользователю наилучшим образом

Если пользователь пишет на другом языке, отвечай на том же языке."""


def create_prompt(
    user_message: str,
    history: list[dict[str, Any]] | None = None,
    system_prompt: str | None = None,
) -> list[dict[str, str]]:
    """Create prompt messages for LLM request.

    Args:
        user_message: Current user message
        history: Previous conversation history
        system_prompt: Custom system prompt (optional)

    Returns:
        List of message dictionaries for LLM API
    """
    if history is None:
        history = []

    if system_prompt is None:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": user_message},
    ]

    logger.debug("Created prompt with %d messages", len(messages))
    return messages


def validate_message_format(message: dict[str, Any]) -> bool:
    """Validate message format for LLM API.

    Args:
        message: Message dictionary to validate

    Returns:
        True if message format is valid, False otherwise
    """
    if not isinstance(message, dict):
        return False

    if "role" not in message or "content" not in message:
        return False

    valid_roles = {"system", "user", "assistant"}
    if message["role"] not in valid_roles:
        return False

    return not (not isinstance(message["content"], str) or not message["content"].strip())


def validate_history(history: list[dict[str, Any]]) -> bool:
    """Validate conversation history format.

    Args:
        history: List of message dictionaries

    Returns:
        True if all messages are valid, False otherwise
    """
    if not isinstance(history, list):
        return False

    for message in history:
        if not validate_message_format(message):
            logger.warning("Invalid message format in history: %s", message)
            return False

    return True


def create_system_message(content: str) -> dict[str, str]:
    """Create a system message.

    Args:
        content: System message content

    Returns:
        Formatted system message
    """
    return {"role": "system", "content": content}


def create_user_message(content: str) -> dict[str, str]:
    """Create a user message.

    Args:
        content: User message content

    Returns:
        Formatted user message
    """
    return {"role": "user", "content": content}


def create_assistant_message(content: str) -> dict[str, str]:
    """Create an assistant message.

    Args:
        content: Assistant message content

    Returns:
        Formatted assistant message
    """
    return {"role": "assistant", "content": content}

