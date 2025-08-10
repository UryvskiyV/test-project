"""Tests for configuration module."""

import os

import pytest

from src.config import get_env_var


class TestConfig:
    """Test cases for configuration functions."""

    def test_get_env_var_existing(self) -> None:
        """Test getting existing environment variable."""
        # Set test environment variable
        test_key = "TEST_ENV_VAR"
        test_value = "test_value"
        os.environ[test_key] = test_value

        try:
            result = get_env_var(test_key)
            assert result == test_value
        finally:
            # Clean up
            del os.environ[test_key]

    def test_get_env_var_with_default(self) -> None:
        """Test getting non-existing environment variable with default."""
        test_key = "NON_EXISTING_ENV_VAR"
        default_value = "default_value"

        result = get_env_var(test_key, default_value)
        assert result == default_value

    def test_get_env_var_missing_required(self) -> None:
        """Test getting required environment variable that doesn't exist."""
        test_key = "REQUIRED_MISSING_ENV_VAR"

        error_msg = f"Environment variable {test_key} is required"
        with pytest.raises(ValueError, match=error_msg):
            get_env_var(test_key)
