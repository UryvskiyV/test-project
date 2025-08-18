"""Prompts module for LLM interactions."""

from typing import Any

from src.logging_config import get_logger

logger = get_logger(__name__)

# Default system prompt for the assistant
DEFAULT_SYSTEM_PROMPT = """Ты - умный и полезный ИИ-помощник в Telegram боте. Твоя задача - быть максимально полезным, отвечая на вопросы пользователей и помогая им решать различные задачи.

🎯 ОСНОВНЫЕ ПРИНЦИПЫ:
- Отвечай точно и информативно, но кратко
- Используй дружелюбный и профессиональный тон
- Структурируй ответы для лучшего восприятия
- Если не знаешь ответ - честно признайся и предложи альтернативы
- Никогда не выдумывай факты или данные

📝 ФОРМАТИРОВАНИЕ:
- Используй эмодзи для лучшего визуального восприятия (умеренно)
- Применяй форматирование Markdown когда это уместно
- Разбивай длинные ответы на пункты или абзацы
- Выделяй ключевую информацию

🌍 ЯЗЫКИ:
- По умолчанию отвечай на русском языке
- Если пользователь пишет на другом языке, адаптируйся к его языку
- Поддерживай многоязычное общение

🧠 КОНТЕКСТ:
- Помни предыдущие сообщения в диалоге
- Учитывай контекст при формулировке ответов
- Развивай тему разговора логично
- Задавай уточняющие вопросы если нужно больше информации

🚀 СПЕЦИАЛИЗАЦИЯ:
- Программирование и технологии
- Обучение и образование  
- Повседневные вопросы и советы
- Творческие задачи
- Анализ и решение проблем

Будь полезным, умным и приятным собеседником!"""


def create_prompt(
    user_message: str,
    history: list[dict[str, Any]] | None = None,
    system_prompt: str | None = None,
) -> list[dict[str, str]]:
    """Create prompt messages for LLM request.

    Args:
        user_message: Current user message
        history: Previous conversation history
        system_prompt: Custom system prompt (optional)

    Returns:
        List of message dictionaries for LLM API
    """
    if history is None:
        history = []

    if system_prompt is None:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": user_message},
    ]

    logger.debug("Created prompt with %d messages", len(messages))
    return messages


def validate_message_format(message: dict[str, Any]) -> bool:
    """Validate message format for LLM API.

    Args:
        message: Message dictionary to validate

    Returns:
        True if message format is valid, False otherwise
    """
    if not isinstance(message, dict):
        return False

    if "role" not in message or "content" not in message:
        return False

    valid_roles = {"system", "user", "assistant"}
    if message["role"] not in valid_roles:
        return False

    return not (not isinstance(message["content"], str) or not message["content"].strip())


def validate_history(history: list[dict[str, Any]]) -> bool:
    """Validate conversation history format.

    Args:
        history: List of message dictionaries

    Returns:
        True if all messages are valid, False otherwise
    """
    if not isinstance(history, list):
        return False

    for message in history:
        if not validate_message_format(message):
            logger.warning("Invalid message format in history: %s", message)
            return False

    return True


def create_system_message(content: str) -> dict[str, str]:
    """Create a system message.

    Args:
        content: System message content

    Returns:
        Formatted system message
    """
    return {"role": "system", "content": content}


def create_user_message(content: str) -> dict[str, str]:
    """Create a user message.

    Args:
        content: User message content

    Returns:
        Formatted user message
    """
    return {"role": "user", "content": content}


def create_assistant_message(content: str) -> dict[str, str]:
    """Create an assistant message.

    Args:
        content: Assistant message content

    Returns:
        Formatted assistant message
    """
    return {"role": "assistant", "content": content}


def create_adaptive_system_prompt(history: list[dict[str, Any]] | None = None) -> str:
    """Create an adaptive system prompt based on conversation history.
    
    Args:
        history: Previous conversation history
        
    Returns:
        Adaptive system prompt text
    """
    base_prompt = DEFAULT_SYSTEM_PROMPT
    
    if not history:
        return base_prompt
    
    # Analyze conversation context
    context_hints = []
    
    # Check if conversation involves programming/technical topics
    tech_keywords = ["код", "программ", "python", "javascript", "bug", "api", "database", "алгоритм"]
    if _contains_keywords(history, tech_keywords):
        context_hints.append("\n💻 ТЕКУЩИЙ КОНТЕКСТ: Техническое обсуждение - предоставляй детальные технические решения с примерами кода когда уместно.")
    
    # Check if conversation involves learning/education
    learning_keywords = ["учить", "изучать", "понять", "объясни", "как работает", "что такое"]
    if _contains_keywords(history, learning_keywords):
        context_hints.append("\n📚 ТЕКУЩИЙ КОНТЕКСТ: Обучающий диалог - используй пошаговые объяснения, примеры и проверь понимание.")
    
    # Check if conversation involves problem-solving
    problem_keywords = ["проблема", "ошибка", "не работает", "помоги", "решить", "исправить"]
    if _contains_keywords(history, problem_keywords):
        context_hints.append("\n🔧 ТЕКУЩИЙ КОНТЕКСТ: Решение проблемы - структурируй диагностику проблемы и предложи конкретные шаги решения.")
    
    # Check conversation length for context management
    if len(history) > 10:
        context_hints.append("\n💭 КОНТЕКСТ: Длинный диалог - кратко резюмируй ключевые моменты если нужно, избегай повторений.")
    
    if context_hints:
        return base_prompt + "\n".join(context_hints)
    
    return base_prompt


def _contains_keywords(history: list[dict[str, Any]], keywords: list[str]) -> bool:
    """Check if conversation history contains specific keywords.
    
    Args:
        history: Conversation history
        keywords: List of keywords to search for
        
    Returns:
        True if any keywords found in recent messages
    """
    # Check last 5 messages for relevance
    recent_messages = history[-5:] if len(history) > 5 else history
    
    for message in recent_messages:
        if message.get("role") in ("user", "assistant"):
            content = message.get("content", "").lower()
            if any(keyword.lower() in content for keyword in keywords):
                return True
    
    return False

