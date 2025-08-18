"""Dialog context manager for LLM integration."""

from typing import Any

from src.dialog.storage import (
    add_assistant_message,
    add_user_message,
    get_user_dialog_messages,
    reset_user_dialog,
)
from src.llm.prompts import create_adaptive_system_prompt
from src.logging_config import get_logger

logger = get_logger(__name__)

# Configuration for context management
DEFAULT_CONTEXT_LIMIT = 10  # Maximum number of recent messages to include
MAX_CONTEXT_TOKENS = 2000   # Approximate token limit for context


def prepare_context_for_llm(user_id: str, limit: int | None = None) -> list[dict[str, str]]:
    """Prepare dialog context for LLM request.
    
    Args:
        user_id: Telegram user ID
        limit: Maximum number of recent messages to include
        
    Returns:
        List of messages formatted for LLM (without timestamps)
    """
    if limit is None:
        limit = DEFAULT_CONTEXT_LIMIT
    
    # Get recent messages from user's dialog
    messages = get_user_dialog_messages(user_id, limit)
    
    # Convert to LLM format (remove timestamps)
    llm_messages = []
    for message in messages:
        llm_message = {
            "role": message["role"],
            "content": message["content"],
        }
        llm_messages.append(llm_message)
    
    logger.debug("Prepared %d messages for LLM context for user %s", len(llm_messages), user_id)
    return llm_messages


def estimate_context_size(messages: list[dict[str, str]]) -> int:
    """Estimate approximate token count for messages.
    
    Args:
        messages: List of messages
        
    Returns:
        Approximate token count
    """
    # Simple estimation: ~4 characters per token
    total_chars = sum(len(msg["content"]) for msg in messages)
    estimated_tokens = total_chars // 4
    
    return estimated_tokens


def trim_context_if_needed(messages: list[dict[str, str]], max_tokens: int | None = None) -> list[dict[str, str]]:
    """Trim context if it exceeds token limit.
    
    Args:
        messages: List of messages
        max_tokens: Maximum allowed tokens
        
    Returns:
        Trimmed list of messages
    """
    if max_tokens is None:
        max_tokens = MAX_CONTEXT_TOKENS
    
    # Start with all messages and trim from the beginning if needed
    current_messages = messages[:]
    
    while current_messages and estimate_context_size(current_messages) > max_tokens:
        # Remove the oldest message (but keep at least the last one)
        if len(current_messages) > 1:
            current_messages.pop(0)
            logger.debug("Trimmed context: removed oldest message")
        else:
            break
    
    if len(current_messages) < len(messages):
        logger.info("Context trimmed from %d to %d messages", len(messages), len(current_messages))
    
    return current_messages


def save_user_interaction(user_id: str, user_message: str, assistant_response: str) -> None:
    """Save user interaction to dialog storage.
    
    Args:
        user_id: Telegram user ID
        user_message: User's message
        assistant_response: Assistant's response
    """
    # Save user message
    user_saved = add_user_message(user_id, user_message)
    if not user_saved:
        logger.error("Failed to save user message for user %s", user_id)
        return
    
    # Save assistant response
    assistant_saved = add_assistant_message(user_id, assistant_response)
    if not assistant_saved:
        logger.error("Failed to save assistant message for user %s", user_id)
        return
    
    logger.debug("Saved interaction for user %s", user_id)


def reset_user_context(user_id: str) -> None:
    """Reset user's dialog context.
    
    Args:
        user_id: Telegram user ID
    """
    new_dialog_id = reset_user_dialog(user_id)
    logger.info("Reset context for user %s, new dialog: %s", user_id, new_dialog_id)


def get_context_summary(user_id: str) -> dict[str, Any]:
    """Get summary of user's dialog context.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Dictionary with context information
    """
    messages = get_user_dialog_messages(user_id)
    
    user_messages = [msg for msg in messages if msg["role"] == "user"]
    assistant_messages = [msg for msg in messages if msg["role"] == "assistant"]
    
    summary = {
        "total_messages": len(messages),
        "user_messages": len(user_messages),
        "assistant_messages": len(assistant_messages),
        "estimated_tokens": estimate_context_size(messages),
        "has_context": len(messages) > 0,
    }
    
    return summary


def get_optimized_context_for_llm(user_id: str) -> tuple[list[dict[str, str]], str]:
    """Get optimized context for LLM with automatic trimming and adaptive prompt.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Tuple of (optimized message list, adaptive system prompt)
    """
    # Get recent messages
    context = prepare_context_for_llm(user_id)
    
    # Trim if needed
    optimized_context = trim_context_if_needed(context)
    
    # Create adaptive system prompt based on conversation history
    adaptive_prompt = create_adaptive_system_prompt(optimized_context)
    
    logger.debug("Optimized context for user %s: %d messages, ~%d tokens, adaptive prompt: %s", 
                user_id, len(optimized_context), estimate_context_size(optimized_context),
                "yes" if adaptive_prompt != create_adaptive_system_prompt() else "no")
    
    return optimized_context, adaptive_prompt
