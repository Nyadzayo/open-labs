"""Test data factories and assertion helpers for fintech labs."""

from __future__ import annotations

import uuid
from decimal import Decimal


def make_payment_request(
    amount: str = "50.00",
    currency: str = "USD",
    recipient: str = "merchant_42",
) -> dict:
    """Create a payment request payload."""
    return {
        "amount": amount,
        "currency": currency,
        "recipient": recipient,
    }


def make_idempotency_key() -> str:
    """Generate a unique idempotency key."""
    return f"idem-{uuid.uuid4().hex[:12]}"


def assert_payment_response(response_json: dict) -> None:
    """Assert a response has the expected payment shape."""
    assert "id" in response_json
    assert "status" in response_json
    assert "amount" in response_json
    assert Decimal(response_json["amount"]) > 0
