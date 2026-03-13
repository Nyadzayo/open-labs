"""Token bucket rate limiter."""

from __future__ import annotations

import time


class RateLimiter:
    """Token bucket rate limiter with per-key tracking."""

    def __init__(self, max_tokens: int, refill_rate: float) -> None:
        """
        Args:
            max_tokens: Maximum tokens per bucket.
            refill_rate: Tokens added per second.
        """
        self._max_tokens = max_tokens
        self._refill_rate = refill_rate
        self._tokens: dict[str, float] = {}
        self._last_refill: dict[str, float] = {}

    def allow(self, key: str) -> bool:
        """Check if request is allowed. Consumes one token if allowed."""
        now = time.monotonic()

        if key not in self._tokens:
            self._tokens[key] = float(self._max_tokens)
            self._last_refill[key] = now

        # Refill tokens based on elapsed time
        elapsed = now - self._last_refill[key]
        self._tokens[key] = min(
            float(self._max_tokens),
            self._tokens[key] + elapsed * self._refill_rate,
        )
        self._last_refill[key] = now

        if self._tokens[key] >= 1.0:
            self._tokens[key] -= 1.0
            return True
        return False

    def remaining(self, key: str) -> int:
        """Tokens remaining for key (without consuming)."""
        return int(self._tokens.get(key, float(self._max_tokens)))
