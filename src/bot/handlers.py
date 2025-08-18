"""Bot handlers for Telegram commands and messages."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.llm.service import LLMError, send_to_llm
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
        "Я - Telegram бот с интеграцией LLM (ИИ).\n"
        "Теперь я умею отвечать на ваши вопросы с помощью искусственного интеллекта!\n\n"
        "Доступные команды:\n"
        "/start - Показать это сообщение\n"
        "/help - Показать справку\n\n"
        "Просто напишите мне любой вопрос, и я постараюсь помочь! 🚀"
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
        "ℹ️ Текущая версия: v0.2.0 (Интеграция с LLM)\n\n"
        "🤖 Теперь бот может:\n"
        "• Отвечать на любые вопросы с помощью ИИ\n"
        "• Помогать с различными задачами\n"
        "• Поддерживать диалог на русском и других языках\n\n"
        "Просто напишите любое сообщение, и я отвечу!"
    )

    await message.answer(help_text)


@router.message()
async def handle_user_message(message: Message) -> None:
    """Handle user messages and send them to LLM.

    Args:
        message: Telegram message object
    """
    user_id = message.from_user.id if message.from_user else "unknown"
    message_text = message.text or ""

    # Skip non-text messages
    if not message_text:
        await message.answer("Извините, я пока умею работать только с текстовыми сообщениями.")
        return

    logger.info(f"User {user_id} sent message: {message_text[:50]}...")

    # Show typing indicator
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Send message to LLM
        llm_response = send_to_llm(message_text)

        # Send LLM response back to user
        await message.answer(llm_response)

        logger.info(f"LLM response sent to user {user_id}")

    except LLMError as e:
        logger.error(f"LLM error for user {user_id}: {e}")

        error_response = (
            "😔 Извините, произошла ошибка при обработке вашего сообщения.\n\n"
            "Возможные причины:\n"
            "• Проблемы с подключением к ИИ\n"
            "• Временная недоступность сервиса\n\n"
            "Попробуйте ещё раз через несколько секунд."
        )
        await message.answer(error_response)

    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")

        await message.answer(
            "🚧 Произошла неожиданная ошибка. "
            "Попробуйте позже или обратитесь к администратору."
        )
