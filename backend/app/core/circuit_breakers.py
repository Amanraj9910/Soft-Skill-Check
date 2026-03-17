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
