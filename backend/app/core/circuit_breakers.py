"""
Circuit breakers for external API calls.
Prevents cascading failures when Azure OpenAI or other services are degraded.

Pattern:
  CLOSED (normal) → 10 failures → OPEN (fail fast for 15s) → HALF-OPEN (1 trial) → CLOSED/OPEN

Tuning rationale:
  - fail_max=10: Azure rate-limit 429s arrive in bursts and are transient, not outages.
    A threshold of 5 trips too quickly during normal traffic spikes.
  - reset_timeout=15: 15s is enough for Azure to clear a rate-limit window while
    keeping user-perceived downtime short.
  - Excluded exceptions: Transient errors (rate limits, timeouts, connection resets)
    should NOT trip the breaker — only persistent service failures should.

NOTE: pybreaker's built-in call_async() requires Tornado (gen.coroutine).
      Use `call_async_native()` below instead — it works with standard asyncio.
"""
import pybreaker
from app.core.logging import error_logger


class _BreakerListener(pybreaker.CircuitBreakerListener):
    """Log state transitions for observability."""

    def state_change(self, cb, old_state, new_state):
        error_logger.warning(
            f"⚡ Circuit breaker [{cb.name}]: {old_state.name} → {new_state.name}"
        )


_listener = _BreakerListener()

# Exceptions that are transient / throttling, NOT real outages
_transient_exclude = [
    KeyError,           # Programming errors, not service issues
    ValueError,
    TimeoutError,       # Network timeout — transient
    ConnectionError,    # Connection reset — transient
    ConnectionResetError,
]

# Azure OpenAI circuit breaker
openai_breaker = pybreaker.CircuitBreaker(
    fail_max=10,           # Open after 10 consecutive failures (not transient)
    reset_timeout=15,      # Try again after 15 seconds
    name="azure_openai",
    listeners=[_listener],
    exclude=_transient_exclude,
)

# Azure Speech circuit breaker (STT/TTS)
speech_breaker = pybreaker.CircuitBreaker(
    fail_max=10,
    reset_timeout=15,
    name="azure_speech",
    listeners=[_listener],
    exclude=_transient_exclude,
)

# Azure Blob Storage circuit breaker
blob_breaker = pybreaker.CircuitBreaker(
    fail_max=10,
    reset_timeout=15,
    name="azure_blob",
    listeners=[_listener],
    exclude=_transient_exclude,
)


async def call_async_native(breaker: pybreaker.CircuitBreaker, async_func, *args, **kwargs):
    """
    Native asyncio replacement for pybreaker's call_async().

    pybreaker.call_async() requires Tornado (gen.coroutine) which we don't
    have installed. This wrapper provides the same circuit-breaker semantics
    using standard Python async/await.

    Usage:
        result = await call_async_native(blob_breaker, asyncio.to_thread, sync_fn, arg1, arg2)
    """
    # Let the breaker state decide whether to allow the call (raises CircuitBreakerError if OPEN)
    with breaker._lock:
        breaker.state.before_call(breaker, async_func, *args, **kwargs)

    try:
        result = await async_func(*args, **kwargs)
        # Record success (on_success takes no args beyond self)
        with breaker._lock:
            breaker.state.on_success()
        return result
    except Exception as e:
        # Check if exception is in the exclude list
        excluded = type(e) in breaker._excluded_exceptions
        if not excluded:
            # Record failure — on_failure(exc) takes just the exception
            with breaker._lock:
                breaker.state.on_failure(e)
        raise

