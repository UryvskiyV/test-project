"""Bot handlers for Telegram commands and messages."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.logging_config import get_logger

logger = get_logger(__name__)

# Create router for handlers
router = Router()


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    """Handle /start command.

    Args:
        message: Telegram message object
    """
    user_id = message.from_user.id if message.from_user else "unknown"
    username = message.from_user.username if message.from_user else "unknown"

    logger.info(f"User {user_id} (@{username}) started the bot")

    welcome_text = (
        "🤖 Добро пожаловать!\n\n"
        "Я - простой Telegram бот с интеграцией LLM.\n"
        "Пока что я умею только отвечать на базовые команды.\n\n"
        "Доступные команды:\n"
        "/start - Показать это сообщение\n"
        "/help - Показать справку\n\n"
        "В будущих версиях я научусь общаться с помощью ИИ! 🚀"
    )

    await message.answer(welcome_text)


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Handle /help command.

    Args:
        message: Telegram message object
    """
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info(f"User {user_id} requested help")

    help_text = (
        "📚 Справка по боту\n\n"
        "🔹 /start - Перезапустить бота и показать приветствие\n"
        "🔹 /help - Показать это сообщение с описанием команд\n\n"
        "ℹ️ Текущая версия: v0.1.0 (Базовый функционал)\n\n"
        "В этой версии бот может только отвечать на команды.\n"
        "Интеграция с ИИ будет добавлена в следующих итерациях.\n\n"
        "Если у вас есть вопросы - обратитесь к разработчику."
    )

    await message.answer(help_text)


@router.message()
async def handle_unknown_message(message: Message) -> None:
    """Handle all other messages.

    Args:
        message: Telegram message object
    """
    user_id = message.from_user.id if message.from_user else "unknown"
    message_text = message.text or "non-text message"

    logger.info(f"User {user_id} sent message: {message_text[:50]}...")

    response_text = (
        "🤔 Пока что я не умею обрабатывать обычные сообщения.\n\n"
        "Используйте доступные команды:\n"
        "/start - Перезапустить бота\n"
        "/help - Показать справку\n\n"
        "Интеграция с ИИ будет добавлена в следующих версиях! 🔄"
    )

    await message.answer(response_text)
