"""LLM service module for handling AI interactions."""

import time
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai import APIError, RateLimitError, APIConnectionError, APITimeoutError

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


class LLMRateLimitError(LLMError):
    """Exception for LLM rate limit issues."""


class LLMTimeoutError(LLMError):
    """Exception for LLM timeout issues."""


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

    except (LLMRateLimitError, LLMTimeoutError, LLMConnectionError):
        # Re-raise specific LLM errors without wrapping
        raise
    except Exception as e:
        logger.error("LLM request failed: %s", e)
        raise LLMError(f"LLM request failed: {e}") from e


def _make_llm_request_with_retry(
    client: OpenAI,
    messages: list[dict[str, str]],
    config: dict[str, Any],
    max_retries: int = 3,
) -> ChatCompletion:
    """Make LLM request with smart retry logic based on error type.

    Args:
        client: OpenAI client instance
        messages: Messages to send to LLM
        config: LLM configuration
        max_retries: Maximum number of retry attempts

    Returns:
        LLM response

    Raises:
        LLMRateLimitError: If rate limit is exceeded
        LLMTimeoutError: If request times out
        LLMConnectionError: If connection fails
        LLMError: For other API errors
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return client.chat.completions.create(
                messages=messages,
                **config,
            )

        except RateLimitError as e:
            last_exception = e
            if attempt < max_retries:
                # Longer delay for rate limits
                delay = min(60, 10 * (2 ** attempt))  # 10s, 20s, 40s, max 60s
                logger.warning(
                    "Rate limit hit on attempt %d, retrying in %ds: %s",
                    attempt + 1,
                    delay,
                    e,
                )
                time.sleep(delay)
            else:
                logger.error("Rate limit exceeded after all attempts")
                raise LLMRateLimitError("API rate limit exceeded") from e

        except (APIConnectionError, APITimeoutError) as e:
            last_exception = e
            if attempt < max_retries:
                # Standard delay for connection/timeout issues
                delay = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    "Connection/timeout error on attempt %d, retrying in %ds: %s",
                    attempt + 1,
                    delay,
                    e,
                )
                time.sleep(delay)
            else:
                error_type = "timeout" if isinstance(e, APITimeoutError) else "connection"
                logger.error(f"API {error_type} error after all attempts")
                if isinstance(e, APITimeoutError):
                    raise LLMTimeoutError("API request timed out") from e
                else:
                    raise LLMConnectionError("API connection failed") from e

        except APIError as e:
            last_exception = e
            # For other API errors, only retry if it's potentially temporary
            if attempt < max_retries and _is_retryable_api_error(e):
                delay = 2 ** attempt
                logger.warning(
                    "API error on attempt %d, retrying in %ds: %s",
                    attempt + 1,
                    delay,
                    e,
                )
                time.sleep(delay)
            else:
                logger.error("Non-retryable API error or max attempts reached: %s", e)
                raise LLMError(f"API error: {e}") from e

        except Exception as e:
            last_exception = e
            logger.error("Unexpected error on attempt %d: %s", attempt + 1, e)
            # Don't retry unexpected errors
            raise LLMError(f"Unexpected error: {e}") from e

    # This should not be reached due to exception handling above
    raise LLMError("Max retry attempts exceeded") from last_exception


def _is_retryable_api_error(error: APIError) -> bool:
    """Check if an API error is potentially retryable.
    
    Args:
        error: The API error to check
        
    Returns:
        True if the error might be temporary and worth retrying
    """
    # Common temporary error indicators
    retryable_status_codes = {500, 502, 503, 504}  # Server errors
    retryable_error_types = {"server_error", "timeout", "connection_error"}
    
    # Check status code
    if hasattr(error, 'status_code') and error.status_code in retryable_status_codes:
        return True
    
    # Check error message for common temporary issues
    error_msg = str(error).lower()
    if any(err_type in error_msg for err_type in retryable_error_types):
        return True
    
    return False


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

