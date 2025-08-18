"""OpenRouter client module."""

from openai import OpenAI

from src.config import (
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
)
from src.logging_config import get_logger

logger = get_logger(__name__)


def create_openrouter_client() -> OpenAI:
    """Create and configure OpenRouter client.

    Returns:
        Configured OpenAI client for OpenRouter

    Raises:
        ValueError: If API key is missing or invalid
    """
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "test_key":
        msg = "OpenRouter API key is required for LLM functionality"
        raise ValueError(msg)

    logger.info("Creating OpenRouter client")

    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )

    logger.info("OpenRouter client created successfully")
    return client


def get_llm_config() -> dict[str, str | float | int]:
    """Get LLM configuration parameters.

    Returns:
        Dictionary with LLM configuration
    """
    config = {
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
        "top_p": LLM_TOP_P,
    }

    logger.debug("LLM config: %s", config)
    return config


def validate_openrouter_connection(client: OpenAI) -> bool:
    """Validate OpenRouter connection by making a test request.

    Args:
        client: OpenRouter client instance

    Returns:
        True if connection is valid, False otherwise
    """
    try:
        logger.info("Validating OpenRouter connection")

        # Make a minimal test request
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1,
        )

        if response and response.choices:
            logger.info("OpenRouter connection validated successfully")
            return True

        logger.warning("OpenRouter connection validation failed: empty response")
        return False

    except Exception as e:
        logger.error("OpenRouter connection validation failed: %s", e)
        return False

