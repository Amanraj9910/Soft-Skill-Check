"""
Global exception handlers for FastAPI.

These handlers ensure consistent error responses and proper logging
for all exception types across the application.
"""
import traceback
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError

from app.core.logging import error_logger, get_emoji
from app.core.exceptions import BaseAppException
from app.core import log_messages


async def base_app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """
    Handle custom application exceptions.
    
    Args:
        request: FastAPI request
        exc: Custom application exception
    
    Returns:
        JSON error response
    """
    # Determine log level based on status code
    emoji = get_emoji(exc.status_code)
    
    if exc.status_code >= 500:
        # Server errors - log with full context and stack trace
        error_logger.error(
            f"{emoji}{exc.message}",
            extra={
                "endpoint": str(request.url.path),
                "method": request.method,
                "context": exc.context,
                "status_code": exc.status_code
            },
            exc_info=True
        )
    elif exc.status_code >= 400:
        # Client errors - log as warning without stack trace
        error_logger.warning(
            f"{emoji}{exc.message}",
            extra={
                "endpoint": str(request.url.path),
                "method": request.method,
                "context": exc.context,
                "status_code": exc.status_code
            }
        )
    
    # Return clean error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "context": exc.context if exc.status_code >= 500 else {}
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPException.
    
    Args:
        request: FastAPI request
        exc: HTTP exception
    
    Returns:
        JSON error response
    """
    emoji = get_emoji(exc.status_code)
    
    # Log based on severity
    if exc.status_code >= 500:
        error_logger.error(
            f"{emoji}HTTP {exc.status_code}: {exc.detail}",
            extra={
                "endpoint": str(request.url.path),
                "method": request.method,
                "status_code": exc.status_code
            }
        )
    elif exc.status_code >= 400:
        error_logger.warning(
            f"{emoji}HTTP {exc.status_code}: {exc.detail}",
            extra={
                "endpoint": str(request.url.path),
                "method": request.method,
                "status_code": exc.status_code
            }
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request
        exc: Validation exception
    
    Returns:
        JSON error response with validation details
    """
    emoji = get_emoji(400)
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append({"field": field, "message": message})
    
    # Log validation error
    error_logger.warning(
        f"{emoji}Request validation failed: {len(errors)} error(s)",
        extra={
            "endpoint": str(request.url.path),
            "method": request.method,
            "validation_errors": errors
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "errors": errors
        }
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all unhandled exceptions (500 Internal Server Error).
    
    This is the catch-all handler for unexpected errors.
    Logs full stack trace for debugging.
    
    Args:
        request: FastAPI request
        exc: Unhandled exception
    
    Returns:
        Generic 500 error response
    """
    emoji = get_emoji(500)
    
    # Get full stack trace
    tb = traceback.format_exc()
    
    # Log error with full context
    error_logger.critical(
        f"{emoji}Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "endpoint": str(request.url.path),
            "method": request.method,
            "exception_type": type(exc).__name__,
            "traceback": tb
        }
    )
    
    # Log full traceback for visibility (already structured via the logger)
    error_logger.critical(f"❌ Full traceback:\n{tb}")
    
    # Return safe generic error (don't expose internal details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "error_id": str(request.url.path)  # Could be replaced with error tracking ID
        }
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Custom application exceptions
    app.add_exception_handler(BaseAppException, base_app_exception_handler)
    
    # FastAPI HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # Catch-all for unhandled exceptions
    app.add_exception_handler(Exception, unhandled_exception_handler)
