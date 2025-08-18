"""Dialog storage module using in-memory Python structures."""

import uuid
from datetime import datetime
from typing import Any

from src.logging_config import get_logger

logger = get_logger(__name__)

# Global in-memory storage for dialogs and user contexts
# Structure according to vision.md
_dialogs: dict[str, dict[str, Any]] = {}
_user_contexts: dict[str, dict[str, Any]] = {}


def create_message(role: str, content: str, timestamp: str | None = None) -> dict[str, str]:
    """Create a message according to vision.md format.
    
    Args:
        role: Message role (user, assistant, system)
        content: Message content
        timestamp: Message timestamp (ISO format)
        
    Returns:
        Formatted message dictionary
    """
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    return {
        "role": role,
        "content": content,
        "timestamp": timestamp,
    }


def create_dialog(user_id: str) -> dict[str, Any]:
    """Create a new dialog according to vision.md structure.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        New dialog dictionary
    """
    dialog_id = str(uuid.uuid4())
    start_time = datetime.now().isoformat()
    
    dialog = {
        "user_id": user_id,
        "start_time": start_time,
        "messages": [],
    }
    
    logger.debug("Created new dialog %s for user %s", dialog_id, user_id)
    return dialog_id, dialog


def get_dialog(dialog_id: str) -> dict[str, Any] | None:
    """Get dialog by ID.
    
    Args:
        dialog_id: Dialog identifier
        
    Returns:
        Dialog dictionary or None if not found
    """
    return _dialogs.get(dialog_id)


def save_dialog(dialog_id: str, dialog: dict[str, Any]) -> None:
    """Save dialog to storage.
    
    Args:
        dialog_id: Dialog identifier
        dialog: Dialog dictionary
    """
    _dialogs[dialog_id] = dialog
    logger.debug("Saved dialog %s with %d messages", dialog_id, len(dialog["messages"]))


def add_message_to_dialog(dialog_id: str, role: str, content: str) -> bool:
    """Add message to dialog.
    
    Args:
        dialog_id: Dialog identifier
        role: Message role (user, assistant, system)
        content: Message content
        
    Returns:
        True if message was added, False if dialog not found
    """
    dialog = get_dialog(dialog_id)
    if dialog is None:
        logger.warning("Dialog %s not found", dialog_id)
        return False
    
    message = create_message(role, content)
    dialog["messages"].append(message)
    save_dialog(dialog_id, dialog)
    
    logger.debug("Added %s message to dialog %s", role, dialog_id)
    return True


def get_dialog_messages(dialog_id: str, limit: int | None = None) -> list[dict[str, str]]:
    """Get messages from dialog.
    
    Args:
        dialog_id: Dialog identifier
        limit: Maximum number of recent messages to return
        
    Returns:
        List of messages or empty list if dialog not found
    """
    dialog = get_dialog(dialog_id)
    if dialog is None:
        return []
    
    messages = dialog["messages"]
    if limit is not None and limit > 0:
        messages = messages[-limit:]
    
    return messages


def create_user_context(user_id: str) -> dict[str, Any]:
    """Create user context according to vision.md structure.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        User context dictionary
    """
    # Create new dialog for the user
    dialog_id, dialog = create_dialog(user_id)
    save_dialog(dialog_id, dialog)
    
    user_context = {
        "user_id": user_id,
        "current_dialog_id": dialog_id,
        "settings": {},
    }
    
    logger.info("Created new user context for user %s with dialog %s", user_id, dialog_id)
    return user_context


def get_user_context(user_id: str) -> dict[str, Any]:
    """Get or create user context.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        User context dictionary
    """
    if user_id not in _user_contexts:
        _user_contexts[user_id] = create_user_context(user_id)
    
    return _user_contexts[user_id]


def save_user_context(user_id: str, context: dict[str, Any]) -> None:
    """Save user context to storage.
    
    Args:
        user_id: Telegram user ID
        context: User context dictionary
    """
    _user_contexts[user_id] = context
    logger.debug("Saved user context for user %s", user_id)


def reset_user_dialog(user_id: str) -> str:
    """Reset user dialog by creating a new one.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        New dialog ID
    """
    context = get_user_context(user_id)
    old_dialog_id = context["current_dialog_id"]
    
    # Create new dialog
    new_dialog_id, new_dialog = create_dialog(user_id)
    save_dialog(new_dialog_id, new_dialog)
    
    # Update user context
    context["current_dialog_id"] = new_dialog_id
    save_user_context(user_id, context)
    
    logger.info("Reset dialog for user %s: %s -> %s", user_id, old_dialog_id, new_dialog_id)
    return new_dialog_id


def get_user_dialog_messages(user_id: str, limit: int | None = None) -> list[dict[str, str]]:
    """Get messages from user's current dialog.
    
    Args:
        user_id: Telegram user ID
        limit: Maximum number of recent messages to return
        
    Returns:
        List of messages from current dialog
    """
    context = get_user_context(user_id)
    dialog_id = context["current_dialog_id"]
    return get_dialog_messages(dialog_id, limit)


def add_user_message(user_id: str, content: str) -> bool:
    """Add user message to current dialog.
    
    Args:
        user_id: Telegram user ID
        content: Message content
        
    Returns:
        True if message was added
    """
    context = get_user_context(user_id)
    dialog_id = context["current_dialog_id"]
    return add_message_to_dialog(dialog_id, "user", content)


def add_assistant_message(user_id: str, content: str) -> bool:
    """Add assistant message to current dialog.
    
    Args:
        user_id: Telegram user ID
        content: Message content
        
    Returns:
        True if message was added
    """
    context = get_user_context(user_id)
    dialog_id = context["current_dialog_id"]
    return add_message_to_dialog(dialog_id, "assistant", content)


def get_storage_stats() -> dict[str, int]:
    """Get storage statistics.
    
    Returns:
        Dictionary with storage statistics
    """
    total_messages = sum(len(dialog["messages"]) for dialog in _dialogs.values())
    
    return {
        "total_dialogs": len(_dialogs),
        "total_users": len(_user_contexts),
        "total_messages": total_messages,
    }


def clear_storage() -> None:
    """Clear all storage (for testing purposes).
    
    Warning: This will remove all dialogs and user contexts!
    """
    global _dialogs, _user_contexts
    _dialogs.clear()
    _user_contexts.clear()
    logger.warning("Storage cleared - all dialogs and contexts removed")
