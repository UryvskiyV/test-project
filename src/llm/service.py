"""LLM service module for handling AI interactions."""

import time
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletion

from src.llm.client import create_openrouter_client, get_llm_config
from src.llm.prompts import create_prompt, validate_history
from src.logging_config import get_logger

logger = get_logger(__name__)


class LLMError(Exception):
    """Base exception for LLM-related errors."""


class LLMConnectionError(LLMError):
    """Exception for LLM connection issues."""


class LLMValidationError(LLMError):
    """Exception for LLM validation issues."""


def send_to_llm(
    user_message: str,
    history: list[dict[str, Any]] | None = None,
    system_prompt: str | None = None,
    client: OpenAI | None = None,
) -> str:
    """Send message to LLM and get response.

    Args:
        user_message: User's message to send to LLM
        history: Previous conversation history
        system_prompt: Custom system prompt (optional)
        client: OpenAI client instance (optional, will create if None)

    Returns:
        LLM response text

    Raises:
        LLMError: If LLM request fails
        LLMValidationError: If input validation fails
        LLMConnectionError: If connection to LLM fails
    """
    if not user_message or not user_message.strip():
        msg = "User message cannot be empty"
        raise LLMValidationError(msg)

    if history and not validate_history(history):
        msg = "Invalid history format"
        raise LLMValidationError(msg)

    # Create client if not provided
    if client is None:
        try:
            client = create_openrouter_client()
        except Exception as e:
            raise LLMConnectionError(f"Failed to create LLM client: {e}") from e

    # Prepare messages
    messages = create_prompt(user_message, history, system_prompt)
    config = get_llm_config()

    logger.info("Sending request to LLM with %d messages", len(messages))
    logger.debug("LLM request config: %s", config)

    try:
        response = _make_llm_request_with_retry(client, messages, config)
        response_text = _extract_response_text(response)

        logger.info("LLM response received successfully (length: %d)", len(response_text))
        logger.debug("LLM response: %s", response_text[:100] + "..." if len(response_text) > 100 else response_text)

        return response_text

    except Exception as e:
        logger.error("LLM request failed: %s", e)
        raise LLMError(f"LLM request failed: {e}") from e


def _make_llm_request_with_retry(
    client: OpenAI,
    messages: list[dict[str, str]],
    config: dict[str, Any],
    max_retries: int = 3,
) -> ChatCompletion:
    """Make LLM request with exponential backoff retry.

    Args:
        client: OpenAI client instance
        messages: Messages to send to LLM
        config: LLM configuration
        max_retries: Maximum number of retry attempts

    Returns:
        LLM response

    Raises:
        Exception: If all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return client.chat.completions.create(
                messages=messages,
                **config,
            )

        except Exception as e:
            last_exception = e

            if attempt < max_retries:
                delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    "LLM request attempt %d failed, retrying in %ds: %s",
                    attempt + 1,
                    delay,
                    e,
                )
                time.sleep(delay)
            else:
                logger.error("All LLM request attempts failed")

    raise last_exception


def _extract_response_text(response: ChatCompletion) -> str:
    """Extract text from LLM response.

    Args:
        response: LLM response object

    Returns:
        Response text content

    Raises:
        LLMValidationError: If response format is invalid
    """
    if not response or not response.choices:
        msg = "Empty LLM response"
        raise LLMValidationError(msg)

    choice = response.choices[0]
    if not choice.message or not choice.message.content:
        msg = "Invalid LLM response format"
        raise LLMValidationError(msg)

    return choice.message.content.strip()


def validate_llm_response(response_text: str) -> bool:
    """Validate LLM response content.

    Args:
        response_text: Response text to validate

    Returns:
        True if response is valid, False otherwise
    """
    if not response_text or not response_text.strip():
        return False

    # Basic content filtering (can be extended)
    if len(response_text) > 10000:  # Reasonable length limit
        logger.warning("LLM response too long: %d characters", len(response_text))
        return False

    return True

