"""Main entry point for the Telegram LLM bot."""

import asyncio
import sys

from src.bot.bot import start_bot
from src.logging_config import get_logger, setup_logging


async def main() -> None:
    """Main function to start the bot."""
    # Setup logging first
    setup_logging()

    logger = get_logger(__name__)
    logger.info("Starting Telegram LLM Bot")

    try:
        await start_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
