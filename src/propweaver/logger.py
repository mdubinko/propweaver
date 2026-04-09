#!/usr/bin/env python3
"""
PropWeaver logging utilities with custom SUMMARY level.

Provides token-efficient logging for both tests and main application.
SUMMARY level (25) sits between INFO and WARNING for emoji-rich summaries.
Supports SQL logging at DEBUG level and flexible level control.
"""

import logging
import sys
from typing import Any, Optional

# Define SUMMARY level between INFO (20) and WARNING (30)
SUMMARY = 25
logging.addLevelName(SUMMARY, "SUMMARY")


def summary(self, message, *args, **kwargs):
    """Log a summary message at SUMMARY level"""
    if self.isEnabledFor(SUMMARY):
        self._log(SUMMARY, message, args, **kwargs)


# Add summary method to Logger class
logging.Logger.summary = summary


class EmojiFormatter(logging.Formatter):
    """Formatter optimized for token efficiency with emoji support"""

    def __init__(self, include_timestamp: bool = False):
        if include_timestamp:
            fmt = "%(asctime)s [%(levelname)s] %(message)s"
        else:
            fmt = "%(message)s"
        super().__init__(fmt, datefmt="%H:%M:%S")

    def format(self, record):
        # For SUMMARY level, just show the message (assumes it has emoji)
        if record.levelno == SUMMARY:
            return record.getMessage()
        # For DEBUG SQL queries, show minimal formatting
        elif record.levelno == logging.DEBUG and record.getMessage().startswith("🔍"):
            return record.getMessage()
        else:
            return super().format(record)


class PropWeaverLogger:
    """Centralized logger for PropWeaver with level control and SQL debugging"""

    _instance: Optional["PropWeaverLogger"] = None
    _logger: Optional[logging.Logger] = None
    _level: int = logging.INFO

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        """Set up the main PropWeaver logger"""
        self._logger = logging.getLogger("propweaver")
        self._logger.handlers.clear()  # Clear any existing handlers

        # Default to console output
        handler = logging.StreamHandler(sys.stdout)
        formatter = EmojiFormatter(include_timestamp=False)
        handler.setFormatter(formatter)

        self._logger.addHandler(handler)
        self._logger.setLevel(self._level)
        self._logger.propagate = False  # Don't propagate to root logger

    def set_level(self, level: int):
        """Set logging level for all PropWeaver operations"""
        self._level = level
        if self._logger:
            self._logger.setLevel(level)

    def get_level(self) -> int:
        """Get current logging level"""
        return self._level

    def configure_for_tests(self, brief: bool = False):
        """Configure logger for test output"""
        if brief:
            self.set_level(SUMMARY)
            # Use token-efficient formatter
            if self._logger and self._logger.handlers:
                handler = self._logger.handlers[0]
                handler.setFormatter(EmojiFormatter(include_timestamp=False))
        else:
            self.set_level(logging.INFO)

    @property
    def logger(self) -> logging.Logger:
        """Get the logger instance"""
        if self._logger is None:
            self._setup_logger()
        return self._logger

    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        self.logger.info(message, *args, **kwargs)

    def summary(self, message: str, *args, **kwargs):
        """Log summary message (token-efficient)"""
        self.logger.summary(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        self.logger.error(message, *args, **kwargs)

    def sql(self, query: str, params: Any = None, elapsed_ms: Optional[float] = None):
        """Log SQL queries at DEBUG level with parameters and timing"""
        if not self.logger.isEnabledFor(logging.DEBUG):
            return

        # Format SQL for readability
        formatted_query = " ".join(query.strip().split())

        if params and elapsed_ms is not None:
            self.debug(f"🔍 SQL ({elapsed_ms:.1f}ms): {formatted_query} | params: {params}")
        elif params:
            self.debug(f"🔍 SQL: {formatted_query} | params: {params}")
        elif elapsed_ms is not None:
            self.debug(f"🔍 SQL ({elapsed_ms:.1f}ms): {formatted_query}")
        else:
            self.debug(f"🔍 SQL: {formatted_query}")


# Global logger instance
_pg_logger = PropWeaverLogger()


class DetailedFormatter(logging.Formatter):
    """Standard formatter with more detail"""

    def __init__(self):
        super().__init__(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )


def get_logger() -> PropWeaverLogger:
    """Get the global PropWeaver logger instance"""
    return _pg_logger


def set_log_level(level: int):
    """Set the global PropWeaver logging level"""
    _pg_logger.set_level(level)


def get_log_level() -> int:
    """Get the current PropWeaver logging level"""
    return _pg_logger.get_level()


# Legacy function for backward compatibility
def setup_logger(
    name: str = "propweaver",
    level: int = logging.INFO,
    token_efficient: bool = False,
    stream: Optional = None,
) -> logging.Logger:
    """
    Legacy function - use get_logger() instead.
    Set up a logger with PropWeaver conventions.

    Args:
        name: Logger name (default: 'propweaver')
        level: Logging level (default: INFO)
        token_efficient: Use emoji formatter for token efficiency (default: False)
        stream: Output stream (default: sys.stdout)

    Returns:
        Configured logger instance
    """
    _pg_logger.set_level(level)
    if token_efficient:
        _pg_logger.configure_for_tests(brief=True)
    return _pg_logger.logger


def get_test_logger(level: int = logging.INFO, token_efficient: bool = False) -> PropWeaverLogger:
    """
    Get a logger configured for test output.

    Args:
        level: Logging level (use SUMMARY for token-efficient mode)
        token_efficient: Use emoji formatter without timestamps

    Returns:
        PropWeaver logger configured for test output
    """
    _pg_logger.set_level(level)
    if token_efficient:
        _pg_logger.configure_for_tests(brief=True)
    return _pg_logger


def get_app_logger(level: int = logging.INFO) -> PropWeaverLogger:
    """
    Get a logger configured for main application.

    Args:
        level: Logging level

    Returns:
        PropWeaver logger configured for application use
    """
    _pg_logger.set_level(level)
    return _pg_logger


# Convenience function for common test usage patterns
def configure_test_output(brief: bool = False, suppress_warnings: bool = True) -> PropWeaverLogger:
    """
    Configure test output for common usage patterns.

    Args:
        brief: Use SUMMARY level for token-efficient output
        suppress_warnings: Suppress Python warnings during tests

    Returns:
        Configured PropWeaver logger
    """
    if suppress_warnings:
        import warnings

        warnings.filterwarnings("ignore")

    _pg_logger.configure_for_tests(brief=brief)
    return _pg_logger
