"""Main bot module for Telegram integration."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.handlers import router
from src.config import TELEGRAM_BOT_TOKEN
from src.logging_config import get_logger

logger = get_logger(__name__)


def create_bot() -> Bot:
    """Create and configure bot instance.

    Returns:
        Configured Bot instance
    """
    logger.info("Creating bot instance")

    return Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )



def create_dispatcher() -> Dispatcher:
    """Create and configure dispatcher with handlers.

    Returns:
        Configured Dispatcher instance
    """
    logger.info("Creating dispatcher")

    dp = Dispatcher()

    # Include handlers router
    dp.include_router(router)

    logger.info("Handlers registered successfully")

    return dp


async def start_bot() -> None:
    """Start the bot and begin polling."""
    logger.info("Starting Telegram bot")

    # Create bot and dispatcher
    bot = create_bot()
    dp = create_dispatcher()

    try:
        # Get bot info
        bot_info = await bot.get_me()
        logger.info(f"Bot started: @{bot_info.username} ({bot_info.full_name})")

        # Start polling
        logger.info("Starting polling...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        logger.info("Bot stopped")
        await bot.session.close()
