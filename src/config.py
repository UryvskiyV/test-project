"""Configuration module for the bot."""

import os
import sys

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_env_var(name: str, default: str | None = None) -> str:
    """Get environment variable with optional default value.

    Args:
        name: Environment variable name
        default: Default value if variable is not set

    Returns:
        Environment variable value

    Raises:
        ValueError: If required environment variable is not set
    """
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Environment variable {name} is required")
    return value


# Check if we're in test mode
_TESTING = "pytest" in sys.modules

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = get_env_var("TELEGRAM_BOT_TOKEN") if not _TESTING else "test_token"

# OpenRouter API Configuration
OPENROUTER_API_KEY = get_env_var("OPENROUTER_API_KEY") if not _TESTING else "test_key"
OPENROUTER_BASE_URL = get_env_var("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# LLM Configuration
LLM_MODEL = get_env_var("LLM_MODEL", "openai/gpt-3.5-turbo")
LLM_TEMPERATURE = float(get_env_var("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(get_env_var("LLM_MAX_TOKENS", "1000"))
LLM_TOP_P = float(get_env_var("LLM_TOP_P", "0.9"))

# Logging Configuration
LOG_LEVEL = get_env_var("LOG_LEVEL", "INFO")
LOG_FILE = get_env_var("LOG_FILE", "bot.log")

# Application Configuration
DEBUG = get_env_var("DEBUG", "false").lower() == "true"
