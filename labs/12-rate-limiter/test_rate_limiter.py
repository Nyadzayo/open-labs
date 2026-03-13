"""Tests for token bucket rate limiter."""

from __future__ import annotations

import time

import pytest
from rate_limiter import RateLimiter


def test_allows_under_limit() -> None:
    limiter = RateLimiter(max_tokens=5, refill_rate=1.0)
    assert limiter.allow("user_1") is True


def test_rejects_over_limit() -> None:
    limiter = RateLimiter(max_tokens=2, refill_rate=0.0)
    assert limiter.allow("user_1") is True
    assert limiter.allow("user_1") is True
    assert limiter.allow("user_1") is False


def test_independent_per_key() -> None:
    limiter = RateLimiter(max_tokens=1, refill_rate=0.0)
    assert limiter.allow("user_1") is True
    assert limiter.allow("user_2") is True
    assert limiter.allow("user_1") is False
    assert limiter.allow("user_2") is False


def test_tokens_refill(monkeypatch: pytest.MonkeyPatch) -> None:
    limiter = RateLimiter(max_tokens=1, refill_rate=10.0)
    assert limiter.allow("user_1") is True
    assert limiter.allow("user_1") is False

    # Simulate 0.2s passing → 2 tokens at 10/s, capped at 1
    original = time.monotonic()
    monkeypatch.setattr(time, "monotonic", lambda: original + 0.2)
    assert limiter.allow("user_1") is True


def test_max_tokens_cap() -> None:
    limiter = RateLimiter(max_tokens=3, refill_rate=0.0)
    for _ in range(3):
        assert limiter.allow("user_1") is True
    assert limiter.allow("user_1") is False


def test_remaining_count() -> None:
    limiter = RateLimiter(max_tokens=5, refill_rate=0.0)
    assert limiter.remaining("user_1") == 5
    limiter.allow("user_1")
    assert limiter.remaining("user_1") == 4


def test_burst_then_refill(monkeypatch: pytest.MonkeyPatch) -> None:
    limiter = RateLimiter(max_tokens=3, refill_rate=1.0)
    # Use all tokens
    for _ in range(3):
        limiter.allow("user_1")
    assert limiter.allow("user_1") is False

    # After 2 seconds, should have 2 tokens
    original = time.monotonic()
    monkeypatch.setattr(time, "monotonic", lambda: original + 2.0)
    assert limiter.allow("user_1") is True
    assert limiter.allow("user_1") is True
    assert limiter.allow("user_1") is False


def test_zero_refill_rate_never_refills() -> None:
    limiter = RateLimiter(max_tokens=1, refill_rate=0.0)
    assert limiter.allow("user_1") is True
    assert limiter.allow("user_1") is False
    # Even after many calls, still denied
    for _ in range(100):
        assert limiter.allow("user_1") is False
