"""
Request logging middleware for automatic API request/response tracking.

This middleware logs every HTTP request with:
- Request details (method, path, client)
- Response status code
- Execution time
- Human-readable messages with visual indicators
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import api_logger
from app.core import log_messages


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses.
    
    Provides automatic logging with:
    - Human-readable messages
    - Execution timing
    - Status code differentiation (2xx/4xx/5xx)
    - Visual indicators (emojis in development)
    """
    
    def __init__(self, app: ASGIApp, enable_body_logging: bool = False):
        """
        Initialize middleware.
        
        Args:
            app: ASGI application
            enable_body_logging: Whether to log request/response bodies (only in dev)
        """
        super().__init__(app)
        self.enable_body_logging = enable_body_logging
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
        
        Returns:
            HTTP response
        """
        # Skip logging for noisy/infrastructure endpoints
        skip_paths = {"/health", "/", "/status", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}
        if request.url.path in skip_paths:
            return await call_next(request)
        
        # Extract client info
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = str(request.url.path)
        
        # Log incoming request
        api_logger.info(log_messages.request_received(method, path, client_host))
        
        # Process request and measure time
        start_time = time.time()
        
        try:
            response = await call_next(request)
        except Exception as e:
            # If an exception occurs, it will be caught by exception handlers
            # We just measure the time here
            duration_ms = (time.time() - start_time) * 1000
            api_logger.error(
                log_messages.request_completed(method, path, 500, duration_ms)
            )
            raise
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log completed request with appropriate level
        status_code = response.status_code
        
        if 200 <= status_code < 300:
            # Success - INFO level
            api_logger.info(
                log_messages.request_completed(method, path, status_code, duration_ms)
            )
        elif 400 <= status_code < 500:
            # Client error - WARNING level
            api_logger.warning(
                log_messages.request_completed(method, path, status_code, duration_ms)
            )
        elif 500 <= status_code < 600:
            # Server error - ERROR level
            api_logger.error(
                log_messages.request_completed(method, path, status_code, duration_ms)
            )
        else:
            # Other status codes
            api_logger.info(
                log_messages.request_completed(method, path, status_code, duration_ms)
            )
        
        return response
