"""Test helpers for webhook processing lab.

Separated from conftest.py so test files can import directly
without relying on pytest's conftest discovery mechanism.
"""

from __future__ import annotations

import json

from crypto import compute_signature

WEBHOOK_SECRET = "test_webhook_secret"


def make_signed_event(
    event_id: str = "evt_001",
    event_type: str = "payment.captured",
    payment_id: str = "pay_123",
) -> tuple[bytes, str]:
    """Create a signed webhook payload. Returns (body_bytes, signature)."""
    body = json.dumps(
        {"event_id": event_id, "type": event_type, "payment_id": payment_id}
    ).encode()
    sig = compute_signature(body, WEBHOOK_SECRET)
    return body, sig
