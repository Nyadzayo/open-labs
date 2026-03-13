"""Resilient HTTP client with retry and circuit breaker."""

from __future__ import annotations

import asyncio
import time
from enum import StrEnum

import httpx


class CircuitState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""


class ResilientClient:
    def __init__(
        self,
        base_url: str,
        max_retries: int = 3,
        base_delay: float = 0.1,
        failure_threshold: int = 3,
        recovery_timeout: float = 5.0,
    ) -> None:
        self._client = httpx.AsyncClient(base_url=base_url)
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._circuit_state = CircuitState.CLOSED
        self._last_failure_time: float | None = None

    @property
    def circuit_state(self) -> CircuitState:
        return self._circuit_state

    async def request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        """Make request with retry + circuit breaker."""
        self._check_circuit()

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = await self._client.request(method, path, **kwargs)
                if resp.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"{resp.status_code}", request=resp.request, response=resp
                    )
                self._on_success()
                return resp
            except (
                httpx.HTTPStatusError,
                httpx.ConnectError,
                httpx.TimeoutException,
            ) as exc:
                last_exc = exc
                is_client_error = (
                    isinstance(exc, httpx.HTTPStatusError)
                    and exc.response.status_code < 500
                )
                if is_client_error:
                    return exc.response
                if attempt < self._max_retries:
                    await asyncio.sleep(self._base_delay * (2**attempt))

        self._on_failure()
        raise last_exc  # type: ignore[misc]

    def _check_circuit(self) -> None:
        if self._circuit_state == CircuitState.OPEN:
            elapsed = (
                time.monotonic() - self._last_failure_time
                if self._last_failure_time
                else 0.0
            )
            if elapsed >= self._recovery_timeout:
                self._circuit_state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError("Circuit breaker is open")

    def _on_success(self) -> None:
        self._failure_count = 0
        self._circuit_state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            self._circuit_state = CircuitState.OPEN

    async def close(self) -> None:
        await self._client.aclose()
