"""HMAC-SHA256 webhook signature verification."""

from __future__ import annotations

import hashlib
import hmac


def compute_signature(payload: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature for a payload."""
    return hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify a webhook signature using constant-time comparison.

    Uses hmac.compare_digest (not ==) to prevent timing attacks.
    """
    expected = compute_signature(payload, secret)
    return hmac.compare_digest(expected, signature)
