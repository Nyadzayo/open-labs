"""Unit tests for HMAC signature verification."""

from __future__ import annotations

from crypto import compute_signature, verify_signature

SECRET = "webhook_secret_key_123"
PAYLOAD = b'{"event_id": "evt_001", "type": "payment.captured"}'


def test_valid_signature_passes() -> None:
    sig = compute_signature(PAYLOAD, SECRET)
    assert verify_signature(PAYLOAD, sig, SECRET)


def test_invalid_signature_fails() -> None:
    assert not verify_signature(PAYLOAD, "invalid_hex_signature", SECRET)


def test_wrong_secret_fails() -> None:
    sig = compute_signature(PAYLOAD, SECRET)
    assert not verify_signature(PAYLOAD, sig, "wrong_secret")


def test_tampered_payload_fails() -> None:
    sig = compute_signature(PAYLOAD, SECRET)
    tampered = b'{"event_id": "evt_001", "type": "payment.refunded"}'
    assert not verify_signature(tampered, sig, SECRET)


def test_empty_payload() -> None:
    sig = compute_signature(b"", SECRET)
    assert verify_signature(b"", sig, SECRET)
