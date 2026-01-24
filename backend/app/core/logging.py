"""
Centralized logging configuration with human-readable, colored output.

This module provides environment-aware logging setup:
- Development: Colored logs with emojis for visual clarity
- Production: Clean structured logs without colors/emojis

Specialized loggers:
- api_logger: API requests and responses
- error_logger: Errors and exceptions
- ai_logger: AI pipeline operations (Speech, OpenAI, etc.)
- db_logger: Database operations
"""
import logging
import sys
from typing import Optional
import colorlog


# Global flag to track if logging has been configured
_logging_configured = False


def configure_logging(
    log_level: str = "INFO",
    enable_colors: bool = True,
    enable_emojis: bool = True
) -> None:
    """
    Configure application-wide logging with colorlog.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_colors: Enable colored output (disable for production)
        enable_emojis: Enable emoji icons (disable for production)
    
    Note:
        This should be called once during application startup.
        In production, set enable_colors=False and enable_emojis=False.
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    # Store emoji preference globally
    if enable_emojis:
        logging.emoji_enabled = True
    else:
        logging.emoji_enabled = False
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = colorlog.StreamHandler(sys.stdout)
    
    if enable_colors:
        # Colored formatter for development
        formatter = colorlog.ColoredFormatter(
            fmt="%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            reset=True,
            style='%'
        )
    else:
        # Plain formatter for production
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # Disable Uvicorn access logs
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)
    
    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (e.g., "api", "error", "ai", "db")
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"soft_skill_check.{name}")


# Pre-configured specialized loggers
api_logger = get_logger("api")
error_logger = get_logger("error")
ai_logger = get_logger("ai")
db_logger = get_logger("db")


def format_duration(milliseconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        milliseconds: Duration in milliseconds
    
    Returns:
        Formatted duration string (e.g., "45 ms", "1.2 s", "2.5 min")
    """
    if milliseconds < 1000:
        return f"{milliseconds:.0f} ms"
    elif milliseconds < 60000:
        return f"{milliseconds / 1000:.1f} s"
    else:
        return f"{milliseconds / 60000:.1f} min"


def get_emoji(status_code: int) -> str:
    """
    Get emoji indicator for HTTP status code.
    
    Args:
        status_code: HTTP status code
    
    Returns:
        Emoji string if enabled, empty string otherwise
    """
    if not getattr(logging, 'emoji_enabled', False):
        return ""
    
    if 200 <= status_code < 300:
        return "🟢 "
    elif 400 <= status_code < 500:
        return "🟡 "
    elif 500 <= status_code < 600:
        return "🔴 "
    else:
        return ""
