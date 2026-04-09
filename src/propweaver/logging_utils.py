"""
Modern logging utilities for PropWeaver library.

Designed to work as a library component that respects the application's
logging configuration through proper logger hierarchy and propagation.
"""

import logging
from typing import Any, Dict, Optional

# Define SUMMARY level between INFO (20) and WARNING (30)
SUMMARY = 25
logging.addLevelName(SUMMARY, "SUMMARY")


def summary(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
    """Log a summary message at SUMMARY level"""
    if self.isEnabledFor(SUMMARY):
        self._log(SUMMARY, message, args, **kwargs)


# Add summary method to Logger class
logging.Logger.summary = summary  # type: ignore


def sql(self: logging.Logger, query: str, params: Any = None, elapsed_ms: Optional[float] = None) -> None:
    """Log SQL queries at DEBUG level with parameters and timing"""
    log_sql_query(query, params, elapsed_ms, component=self.name.split('.')[-1])


# Add sql method to Logger class
logging.Logger.sql = sql  # type: ignore


def get_logger(name: str) -> logging.Logger:
    """
    Get a PropWeaver logger that inherits from application configuration.

    Uses proper logger hierarchy so that the main application can control
    all logging behavior through its dictConfig.

    Args:
        name: Component name (e.g., "storage", "query", "core")

    Returns:
        Logger instance that will inherit from parent "propweaver" logger
    """
    return logging.getLogger(f"propweaver.{name}")


def log_with_context(logger: logging.Logger, level: int, message: str, **context: Any) -> None:
    """
    Log a message with structured context.

    This provides the same pattern as Cogno for consistency across
    the PropWeaver library and main application.

    Args:
        logger: Logger instance
        level: Log level (logging.DEBUG, logging.INFO, etc.)
        message: Log message
        **context: Additional context fields
    """
    record = logger.makeRecord(
        logger.name, level, "", 0, message, (), None
    )
    # Add context as a custom attribute that formatters can use
    record.propweaver_context = context
    logger.handle(record)


# Convenience functions for common PropWeaver logging patterns
def log_storage_operation(operation: str, table: str, node_id: Optional[str] = None,
                         elapsed_ms: Optional[float] = None, **context: Any) -> None:
    """Log storage operations with structured context"""
    logger = get_logger("storage")

    emojis = {
        "insert": "💾", "select": "🔍", "update": "✏️", "delete": "🗑️",
        "create_table": "🏗️", "index": "📇", "transaction": "🔄"
    }
    emoji = emojis.get(operation.lower(), "💾")

    message = f"{emoji} {operation.upper()}"
    if elapsed_ms is not None:
        message += f" ({elapsed_ms:.1f}ms)"

    ctx = {"table": table}
    if node_id:
        ctx["node_id"] = node_id
    ctx.update(context)

    log_with_context(logger, SUMMARY, message, **ctx)


def log_query_operation(operation: str, query_type: str, node_count: Optional[int] = None,
                       elapsed_ms: Optional[float] = None, **context: Any) -> None:
    """Log query operations with structured context"""
    logger = get_logger("query")

    emojis = {
        "traverse": "🚶", "search": "🔍", "filter": "🔎", "aggregate": "📊",
        "pathfind": "🛤️", "subgraph": "🕸️"
    }
    emoji = emojis.get(operation.lower(), "🔍")

    message = f"{emoji} {operation.upper()}"
    if elapsed_ms is not None:
        message += f" ({elapsed_ms:.1f}ms)"

    ctx = {"query_type": query_type}
    if node_count is not None:
        ctx["nodes"] = node_count
    ctx.update(context)

    log_with_context(logger, SUMMARY, message, **ctx)


def log_sql_query(query: str, params: Any = None, elapsed_ms: Optional[float] = None,
                 component: str = "storage") -> None:
    """
    Log SQL queries at DEBUG level with parameters and timing.

    This respects the application's sql_debug configuration by checking
    if DEBUG level is enabled on the logger.
    """
    logger = get_logger(component)
    if not logger.isEnabledFor(logging.DEBUG):
        return

    # Format SQL for readability
    formatted_query = " ".join(query.strip().split())

    if params and elapsed_ms is not None:
        logger.debug(f"🔍 SQL ({elapsed_ms:.1f}ms): {formatted_query} | params: {params}")
    elif params:
        logger.debug(f"🔍 SQL: {formatted_query} | params: {params}")
    elif elapsed_ms is not None:
        logger.debug(f"🔍 SQL ({elapsed_ms:.1f}ms): {formatted_query}")
    else:
        logger.debug(f"🔍 SQL: {formatted_query}")


def log_graph_stats(operation: str, stats: Dict[str, Any], **context: Any) -> None:
    """Log graph statistics and metrics"""
    logger = get_logger("stats")

    message = f"📊 {operation.upper()}"

    # Merge stats into context
    ctx = dict(stats)
    ctx.update(context)

    log_with_context(logger, SUMMARY, message, **ctx)


def log_performance_warning(component: str, operation: str, duration_ms: float,
                          threshold_ms: float = 1000.0, **context: Any) -> None:
    """Log performance warnings for slow operations"""
    if duration_ms < threshold_ms:
        return

    logger = get_logger("performance")

    message = f"⚠️ SLOW {operation.upper()} ({duration_ms:.1f}ms > {threshold_ms:.1f}ms)"

    ctx = {"component": component, "duration_ms": duration_ms, "threshold_ms": threshold_ms}
    ctx.update(context)

    log_with_context(logger, logging.WARNING, message, **ctx)


def log_error_with_context(component: str, error: Exception, operation: str = "",
                          **context: Any) -> None:
    """Log errors with full context for debugging"""
    logger = get_logger(component)

    message = f"💥 ERROR"
    if operation:
        message += f" in {operation.upper()}"
    message += f": {error}"

    ctx = {"error_type": type(error).__name__, "error_msg": str(error)}
    ctx.update(context)

    log_with_context(logger, logging.ERROR, message, **ctx)


# Backward compatibility functions for existing PropWeaver code
def configure_for_tests(brief: bool = False) -> None:
    """
    Configure PropWeaver logging for tests.

    This is a compatibility function. In the new design, the application
    should configure logging via dictConfig which will automatically
    control PropWeaver loggers.
    """
    # For backward compatibility, we'll configure the propweaver root logger
    logger = logging.getLogger("propweaver")

    if brief:
        logger.setLevel(SUMMARY)
    else:
        logger.setLevel(logging.INFO)


def set_log_level(level: int) -> None:
    """
    Set PropWeaver logging level.

    This is a compatibility function. Prefer using the application's
    dictConfig to control PropWeaver logging levels.
    """
    logger = logging.getLogger("propweaver")
    logger.setLevel(level)


def get_log_level() -> int:
    """Get current PropWeaver logging level"""
    logger = logging.getLogger("propweaver")
    return logger.level