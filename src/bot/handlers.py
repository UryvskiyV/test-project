"""Bot handlers for Telegram commands and messages."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.dialog.manager import (
    get_context_summary,
    get_optimized_context_for_llm,
    reset_user_context,
    save_user_interaction,
)
from src.llm.service import LLMError, LLMRateLimitError, LLMTimeoutError, LLMConnectionError, send_to_llm
from src.bot.health import update_telegram_check
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
        "/help - Показать справку\n"
        "/reset - Сбросить контекст диалога\n\n"
        "Просто напишите мне любой вопрос, и я постараюсь помочь! 🚀"
    )

    await message.answer(welcome_text)
    update_telegram_check()  # Track successful Telegram API interaction


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
        "🔹 /help - Показать это сообщение с описанием команд\n"
        "🔹 /reset - Сбросить контекст диалога\n\n"
        "ℹ️ Текущая версия: v0.4.0 (Улучшенная устойчивость и адаптивность)\n\n"
        "🤖 Теперь бот может:\n"
        "• Отвечать на любые вопросы с помощью ИИ\n"
        "• Запоминать контекст диалога для лучшего понимания\n"
        "• Адаптировать стиль общения в зависимости от темы разговора\n"
        "• Устойчиво работать при сбоях API с умными повторными попытками\n"
        "• Поддерживать диалог на русском и других языках\n"
        "• Сбрасывать контекст по команде /reset\n\n"
        "Просто напишите любое сообщение, и я отвечу!"
    )

    await message.answer(help_text)
    update_telegram_check()  # Track successful Telegram API interaction


@router.message(Command("reset"))
async def handle_reset(message: Message) -> None:
    """Handle /reset command to clear dialog context.

    Args:
        message: Telegram message object
    """
    user_id = str(message.from_user.id) if message.from_user else "unknown"
    logger.info(f"User {user_id} requested context reset")

    try:
        # Get context summary before reset
        summary = get_context_summary(user_id)
        
        # Reset user context
        reset_user_context(user_id)
        
        reset_text = (
            "🔄 Контекст диалога сброшен!\n\n"
            f"📊 Было удалено:\n"
            f"• Сообщений: {summary['total_messages']}\n"
            f"• Примерно токенов: {summary['estimated_tokens']}\n\n"
            "Теперь можете начать новый диалог. "
            "Я не буду помнить предыдущие сообщения."
        )
        
        await message.answer(reset_text)
        update_telegram_check()  # Track successful Telegram API interaction
        logger.info(f"Context reset completed for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error resetting context for user {user_id}: {e}")
        await message.answer(
            "❌ Произошла ошибка при сбросе контекста. "
            "Попробуйте ещё раз или обратитесь к администратору."
        )


@router.message()
async def handle_user_message(message: Message) -> None:
    """Handle user messages with context and send them to LLM.

    Args:
        message: Telegram message object
    """
    user_id = str(message.from_user.id) if message.from_user else "unknown"
    message_text = message.text or ""

    # Skip non-text messages
    if not message_text:
        await message.answer("Извините, я пока умею работать только с текстовыми сообщениями.")
        return

    logger.info(f"User {user_id} sent message: {message_text[:50]}...")

    # Show typing indicator
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Get dialog context and adaptive prompt for this user
        context_history, adaptive_prompt = get_optimized_context_for_llm(user_id)
        
        # Send message to LLM with context and adaptive prompt
        llm_response = send_to_llm(message_text, history=context_history, system_prompt=adaptive_prompt)

        # Save the interaction to dialog storage
        save_user_interaction(user_id, message_text, llm_response)

        # Send LLM response back to user
        await message.answer(llm_response)
        update_telegram_check()  # Track successful Telegram API interaction

        # Log context information
        context_summary = get_context_summary(user_id)
        logger.info(f"LLM response sent to user {user_id} with context: {context_summary['total_messages']} messages")

    except LLMRateLimitError as e:
        logger.error(f"Rate limit error for user {user_id}: {e}")
        error_response = (
            "⏱️ Извините, сервис ИИ временно перегружен.\n\n"
            "Пожалуйста, подождите немного и попробуйте снова.\n"
            "Обычно это занимает 1-2 минуты."
        )
        await message.answer(error_response)

    except LLMTimeoutError as e:
        logger.error(f"Timeout error for user {user_id}: {e}")
        error_response = (
            "⏰ Время ожидания ответа от ИИ истекло.\n\n"
            "Возможно, ваш запрос слишком сложный или сервис временно медленно работает.\n"
            "Попробуйте переформулировать вопрос или повторить запрос."
        )
        await message.answer(error_response)

    except LLMConnectionError as e:
        logger.error(f"Connection error for user {user_id}: {e}")
        error_response = (
            "🌐 Проблемы с подключением к сервису ИИ.\n\n"
            "Проверьте подключение к интернету и попробуйте снова.\n"
            "Если проблема повторяется, сервис может быть временно недоступен."
        )
        await message.answer(error_response)

    except LLMError as e:
        logger.error(f"LLM error for user {user_id}: {e}")
        error_response = (
            "😔 Произошла ошибка при обработке вашего сообщения.\n\n"
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
