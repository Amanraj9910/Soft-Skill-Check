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

from app.core.logging import error_logger, get_emoji, get_trace_id, event_log
import logging
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
    trace_id = get_trace_id()
    emoji = get_emoji(exc.status_code)
    
    level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    event_log(
        error_logger, level, "HTTP_EXCEPTION",
        f"{exc.status_code} {exc.detail}  {request.method} {request.url.path}",
        metadata={"status": exc.status_code, "detail": exc.detail,
                  "path": request.url.path, "method": request.method,
                  "trace_id": trace_id},
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "trace_id": trace_id}
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    trace_id = get_trace_id()
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"]})
    
    event_log(
        error_logger, logging.WARNING, "VALIDATION_ERROR",
        f"{len(errors)} validation error(s)  {request.method} {request.url.path}",
        metadata={"path": request.url.path, "errors": errors, "trace_id": trace_id},
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Request validation failed", "errors": errors, "trace_id": trace_id}
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = get_trace_id()
    tb = traceback.format_exc()
    
    event_log(
        error_logger, logging.CRITICAL, "UNHANDLED_EXCEPTION",
        f"{type(exc).__name__}: {exc}  {request.method} {request.url.path}",
        metadata={"path": request.url.path, "method": request.method,
                  "exception_type": type(exc).__name__, "trace_id": trace_id,
                  "stack_trace": tb},
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "trace_id": trace_id,
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
