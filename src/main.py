"""Main entry point for the Telegram LLM bot."""

import asyncio
import sys
import os

from src.bot.bot import start_bot
from src.bot.health import start_health_server, set_bot_status
from src.logging_config import get_logger, setup_logging


async def main() -> None:
    """Main function to start the bot."""
    # Setup logging first
    setup_logging()

    logger = get_logger(__name__)
    logger.info("Starting Telegram LLM Bot")

    # Set initial status
    set_bot_status("starting")

    try:
        # Start health check server for cloud monitoring
        port = int(os.getenv("PORT", "8000"))
        logger.info(f"Starting health server on port {port}")
        
        # Start health server and bot concurrently
        await asyncio.gather(
            start_health_server(port),
            start_bot(),
            return_exceptions=True
        )
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        set_bot_status("stopped")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        set_bot_status("error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
