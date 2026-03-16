"""
Circuit breakers for external API calls.
Prevents cascading failures when Azure OpenAI or other services are degraded.

Pattern:
  CLOSED (normal) → 5 failures → OPEN (fail fast for 30s) → HALF-OPEN (1 trial) → CLOSED/OPEN
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

# Azure OpenAI circuit breaker
openai_breaker = pybreaker.CircuitBreaker(
    fail_max=5,            # Open after 5 consecutive failures
    reset_timeout=30,      # Try again after 30 seconds
    name="azure_openai",
    listeners=[_listener],
    exclude=[              # Don't count these as "failures"
        KeyError,          # Programming errors, not service issues
        ValueError,
    ],
)

# Azure Speech circuit breaker (STT/TTS)
speech_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="azure_speech",
    listeners=[_listener],
)

# Azure Blob Storage circuit breaker
blob_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="azure_blob",
    listeners=[_listener],
)
