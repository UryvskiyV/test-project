"""Logging configuration module."""

import logging
import sys

from src.config import DEBUG, LOG_FILE, LOG_LEVEL


def setup_logging(
    level: str | None = None,
    log_file: str | None = None,
    debug: bool | None = None,
) -> None:
    """Setup logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
        debug: Enable debug mode
    """
    # Use config values as defaults
    level = level or LOG_LEVEL
    log_file = log_file or LOG_FILE
    debug = debug if debug is not None else DEBUG

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (only in production or if explicitly requested)
    if not debug and log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set aiogram logging level to WARNING to reduce noise
    logging.getLogger("aiogram").setLevel(logging.WARNING)

    logging.info("Logging configured successfully")
    logging.info(f"Log level: {level}")
    if not debug and log_file:
        logging.info(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
