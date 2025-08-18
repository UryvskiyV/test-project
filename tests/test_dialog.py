"""Tests for dialog management functionality."""

import pytest
from unittest.mock import patch

from src.dialog.manager import (
    estimate_context_size,
    get_context_summary,
    get_optimized_context_for_llm,
    prepare_context_for_llm,
    reset_user_context,
    save_user_interaction,
    trim_context_if_needed,
)
from src.dialog.storage import (
    add_assistant_message,
    add_message_to_dialog,
    add_user_message,
    clear_storage,
    create_dialog,
    create_message,
    create_user_context,
    get_dialog,
    get_dialog_messages,
    get_storage_stats,
    get_user_context,
    get_user_dialog_messages,
    reset_user_dialog,
    save_dialog,
)


class TestDialogStorage:
    """Test cases for dialog storage functionality."""

    def setup_method(self) -> None:
        """Clear storage before each test."""
        clear_storage()

    def test_create_message(self) -> None:
        """Test message creation."""
        message = create_message("user", "Hello world")
        
        assert message["role"] == "user"
        assert message["content"] == "Hello world"
        assert "timestamp" in message

    def test_create_message_with_timestamp(self) -> None:
        """Test message creation with custom timestamp."""
        timestamp = "2023-06-15T10:30:00"
        message = create_message("assistant", "Hi there", timestamp)
        
        assert message["role"] == "assistant"
        assert message["content"] == "Hi there"
        assert message["timestamp"] == timestamp

    def test_create_dialog(self) -> None:
        """Test dialog creation."""
        user_id = "123456789"
        dialog_id, dialog = create_dialog(user_id)
        
        assert isinstance(dialog_id, str)
        assert dialog["user_id"] == user_id
        assert "start_time" in dialog
        assert dialog["messages"] == []

    def test_save_and_get_dialog(self) -> None:
        """Test saving and retrieving dialog."""
        user_id = "123456789"
        dialog_id, dialog = create_dialog(user_id)
        
        # Save dialog
        save_dialog(dialog_id, dialog)
        
        # Retrieve dialog
        retrieved_dialog = get_dialog(dialog_id)
        assert retrieved_dialog == dialog

    def test_get_nonexistent_dialog(self) -> None:
        """Test getting non-existent dialog."""
        result = get_dialog("nonexistent")
        assert result is None

    def test_add_message_to_dialog(self) -> None:
        """Test adding message to dialog."""
        user_id = "123456789"
        dialog_id, dialog = create_dialog(user_id)
        save_dialog(dialog_id, dialog)
        
        # Add message
        success = add_message_to_dialog(dialog_id, "user", "Hello")
        assert success is True
        
        # Check message was added
        updated_dialog = get_dialog(dialog_id)
        assert len(updated_dialog["messages"]) == 1
        assert updated_dialog["messages"][0]["role"] == "user"
        assert updated_dialog["messages"][0]["content"] == "Hello"

    def test_add_message_to_nonexistent_dialog(self) -> None:
        """Test adding message to non-existent dialog."""
        success = add_message_to_dialog("nonexistent", "user", "Hello")
        assert success is False

    def test_get_dialog_messages(self) -> None:
        """Test getting messages from dialog."""
        user_id = "123456789"
        dialog_id, dialog = create_dialog(user_id)
        save_dialog(dialog_id, dialog)
        
        # Add some messages
        add_message_to_dialog(dialog_id, "user", "Hello")
        add_message_to_dialog(dialog_id, "assistant", "Hi there")
        
        # Get all messages
        messages = get_dialog_messages(dialog_id)
        assert len(messages) == 2
        assert messages[0]["content"] == "Hello"
        assert messages[1]["content"] == "Hi there"

    def test_get_dialog_messages_with_limit(self) -> None:
        """Test getting limited messages from dialog."""
        user_id = "123456789"
        dialog_id, dialog = create_dialog(user_id)
        save_dialog(dialog_id, dialog)
        
        # Add multiple messages
        for i in range(5):
            add_message_to_dialog(dialog_id, "user", f"Message {i}")
        
        # Get limited messages
        messages = get_dialog_messages(dialog_id, limit=3)
        assert len(messages) == 3
        assert messages[0]["content"] == "Message 2"  # Last 3 messages
        assert messages[2]["content"] == "Message 4"

    def test_create_user_context(self) -> None:
        """Test user context creation."""
        user_id = "123456789"
        context = create_user_context(user_id)
        
        assert context["user_id"] == user_id
        assert "current_dialog_id" in context
        assert context["settings"] == {}

    def test_get_user_context(self) -> None:
        """Test getting user context."""
        user_id = "123456789"
        
        # Get context (should create new one)
        context = get_user_context(user_id)
        assert context["user_id"] == user_id
        
        # Get same context again
        same_context = get_user_context(user_id)
        assert same_context == context

    def test_reset_user_dialog(self) -> None:
        """Test resetting user dialog."""
        user_id = "123456789"
        
        # Get initial context
        context = get_user_context(user_id)
        old_dialog_id = context["current_dialog_id"]
        
        # Add some messages
        add_user_message(user_id, "Hello")
        add_assistant_message(user_id, "Hi")
        
        # Reset dialog
        new_dialog_id = reset_user_dialog(user_id)
        
        assert new_dialog_id != old_dialog_id
        
        # Check new context
        new_context = get_user_context(user_id)
        assert new_context["current_dialog_id"] == new_dialog_id
        
        # Check new dialog is empty
        messages = get_user_dialog_messages(user_id)
        assert len(messages) == 0

    def test_add_user_and_assistant_messages(self) -> None:
        """Test adding user and assistant messages."""
        user_id = "123456789"
        
        # Add messages
        user_success = add_user_message(user_id, "How are you?")
        assistant_success = add_assistant_message(user_id, "I'm fine, thanks!")
        
        assert user_success is True
        assert assistant_success is True
        
        # Check messages
        messages = get_user_dialog_messages(user_id)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    def test_get_storage_stats(self) -> None:
        """Test getting storage statistics."""
        # Initial stats
        stats = get_storage_stats()
        assert stats["total_dialogs"] == 0
        assert stats["total_users"] == 0
        assert stats["total_messages"] == 0
        
        # Add some data
        user1 = "123456789"
        user2 = "987654321"
        
        add_user_message(user1, "Hello")
        add_assistant_message(user1, "Hi")
        add_user_message(user2, "How are you?")
        
        # Check updated stats
        stats = get_storage_stats()
        assert stats["total_dialogs"] == 2
        assert stats["total_users"] == 2
        assert stats["total_messages"] == 3


class TestDialogManager:
    """Test cases for dialog manager functionality."""

    def setup_method(self) -> None:
        """Clear storage before each test."""
        clear_storage()

    def test_save_user_interaction(self) -> None:
        """Test saving user interaction."""
        user_id = "123456789"
        user_message = "What's the weather like?"
        assistant_response = "I don't have access to weather data."
        
        save_user_interaction(user_id, user_message, assistant_response)
        
        # Check messages were saved
        messages = get_user_dialog_messages(user_id)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == user_message
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == assistant_response

    def test_prepare_context_for_llm(self) -> None:
        """Test preparing context for LLM."""
        user_id = "123456789"
        
        # Add some messages
        add_user_message(user_id, "Hello")
        add_assistant_message(user_id, "Hi there")
        add_user_message(user_id, "How are you?")
        
        # Prepare context
        context = prepare_context_for_llm(user_id)
        
        assert len(context) == 3
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "Hello"
        assert "timestamp" not in context[0]  # Should be removed for LLM

    def test_prepare_context_with_limit(self) -> None:
        """Test preparing context with limit."""
        user_id = "123456789"
        
        # Add multiple messages
        for i in range(5):
            add_user_message(user_id, f"Message {i}")
        
        # Prepare context with limit
        context = prepare_context_for_llm(user_id, limit=3)
        
        assert len(context) == 3
        assert context[0]["content"] == "Message 2"  # Last 3 messages

    def test_estimate_context_size(self) -> None:
        """Test context size estimation."""
        messages = [
            {"role": "user", "content": "Hello"},      # 5 chars
            {"role": "assistant", "content": "Hi there!"},  # 9 chars
        ]
        
        estimated_tokens = estimate_context_size(messages)
        # (5 + 9) / 4 = 3.5, rounded down to 3
        assert estimated_tokens == 3

    def test_trim_context_if_needed(self) -> None:
        """Test context trimming."""
        # Create messages that exceed token limit
        messages = [
            {"role": "user", "content": "a" * 100},        # ~25 tokens
            {"role": "assistant", "content": "b" * 100},   # ~25 tokens
            {"role": "user", "content": "c" * 100},        # ~25 tokens
        ]
        
        # Trim to 30 tokens max (should remove first two messages)
        trimmed = trim_context_if_needed(messages, max_tokens=30)
        
        # Should keep only last message
        assert len(trimmed) == 1
        assert trimmed[0]["content"] == "c" * 100

    def test_get_context_summary(self) -> None:
        """Test getting context summary."""
        user_id = "123456789"
        
        # Add some messages
        add_user_message(user_id, "Hello")
        add_assistant_message(user_id, "Hi")
        add_user_message(user_id, "How are you?")
        
        summary = get_context_summary(user_id)
        
        assert summary["total_messages"] == 3
        assert summary["user_messages"] == 2
        assert summary["assistant_messages"] == 1
        assert summary["has_context"] is True
        assert summary["estimated_tokens"] > 0

    def test_get_context_summary_empty(self) -> None:
        """Test getting context summary for empty dialog."""
        user_id = "123456789"
        
        summary = get_context_summary(user_id)
        
        assert summary["total_messages"] == 0
        assert summary["user_messages"] == 0
        assert summary["assistant_messages"] == 0
        assert summary["has_context"] is False
        assert summary["estimated_tokens"] == 0

    def test_reset_user_context(self) -> None:
        """Test resetting user context."""
        user_id = "123456789"
        
        # Add some messages
        add_user_message(user_id, "Hello")
        add_assistant_message(user_id, "Hi")
        
        # Check initial context
        summary_before = get_context_summary(user_id)
        assert summary_before["total_messages"] == 2
        
        # Reset context
        reset_user_context(user_id)
        
        # Check context after reset
        summary_after = get_context_summary(user_id)
        assert summary_after["total_messages"] == 0

    def test_get_optimized_context_for_llm(self) -> None:
        """Test getting optimized context for LLM."""
        user_id = "123456789"
        
        # Add messages
        add_user_message(user_id, "Hello")
        add_assistant_message(user_id, "Hi there!")
        
        # Get optimized context (now returns tuple)
        context, adaptive_prompt = get_optimized_context_for_llm(user_id)
        
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "assistant"
        assert "timestamp" not in context[0]
        assert isinstance(adaptive_prompt, str)
        assert "умный и полезный ИИ-помощник" in adaptive_prompt
