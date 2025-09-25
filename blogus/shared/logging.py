"""
Shared logging utilities.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from ..infrastructure.config.settings import get_settings


def setup_logging(logger_name: str = "blogus") -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        logger_name: Name of the logger

    Returns:
        logging.Logger: Configured logger
    """
    settings = get_settings()

    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, settings.logging.level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(settings.logging.format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if configured)
    if settings.logging.file_path:
        try:
            log_path = Path(settings.logging.file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                settings.logging.file_path,
                maxBytes=settings.logging.max_file_size_mb * 1024 * 1024,
                backupCount=settings.logging.backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        except Exception as e:
            logger.error(f"Failed to setup file logging: {e}")

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)