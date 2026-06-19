"""
Circuit breaker pattern for external API calls.
Prevents cascading failures by stopping requests to failing services.
"""

import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker implementation for external API calls.

    Tracks failure counts and opens the circuit when a threshold is exceeded,
    preventing further calls until a timeout period elapses.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        self.total_calls = 0
        self.successful_calls = 0

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function with circuit breaker protection.
        """
        self.total_calls += 1

        if self.state == CircuitState.OPEN:
            if time.time() - (self.last_failure_time or 0) >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info(f"Circuit breaker '{self.name}' moving to half-open state")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open. "
                    f"Retry after {self.recovery_timeout - (time.time() - (self.last_failure_time or 0)):.1f}s"
                )

        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls > self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is in half-open state "
                    f"with max calls ({self.half_open_max_calls}) reached"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle a successful call."""
        self.successful_calls += 1
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.half_open_calls = 0
            logger.info(f"Circuit breaker '{self.name}' recovered to closed state")

    def _on_failure(self):
        """Handle a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker '{self.name}' opened after " f"{self.failure_count} failures"
            )

    async def call_async(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute an async function with circuit breaker protection.
        """
        self.total_calls += 1

        if self.state == CircuitState.OPEN:
            if time.time() - (self.last_failure_time or 0) >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info(f"Circuit breaker '{self.name}' moving to half-open state")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open. "
                    f"Retry after {self.recovery_timeout - (time.time() - (self.last_failure_time or 0)):.1f}s"
                )

        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls > self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is in half-open state "
                    f"with max calls ({self.half_open_max_calls}) reached"
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def reset(self):
        """Reset the circuit breaker to initial state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        logger.info(f"Circuit breaker '{self.name}' manually reset")

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the circuit breaker."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failure_rate": (
                ((self.total_calls - self.successful_calls) / self.total_calls * 100)
                if self.total_calls > 0
                else 0.0
            ),
        }


class CircuitBreakerOpenError(Exception):
    """Raised when a circuit breaker is open and refuses a call."""

    pass


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    """

    _instance: Optional["CircuitBreakerRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._breakers = {}
        return cls._instance

    def get_or_create(self, name: str, **kwargs) -> CircuitBreaker:
        """Get an existing circuit breaker or create a new one."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name=name, **kwargs)
        return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name."""
        return self._breakers.get(name)

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers."""
        return {name: breaker.get_state() for name, breaker in self._breakers.items()}

    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()


breaker_registry = CircuitBreakerRegistry()
