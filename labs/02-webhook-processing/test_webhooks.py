"""Integration tests for webhook processing endpoint."""

from __future__ import annotations

import pytest
from crypto import compute_signature
from httpx import AsyncClient
from test_helpers import WEBHOOK_SECRET, make_signed_event


@pytest.mark.asyncio
async def test_valid_signature_accepted(client: AsyncClient) -> None:
    body, sig = make_signed_event()
    resp = await client.post(
        "/webhooks/payments",
        content=body,
        headers={
            "X-Webhook-Signature": sig,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_invalid_signature_rejected(client: AsyncClient) -> None:
    body, _ = make_signed_event()
    resp = await client.post(
        "/webhooks/payments",
        content=body,
        headers={
            "X-Webhook-Signature": "bad_signature",
            "Content-Type": "application/json",
        },
    )
    # Always returns 200 (don't leak info), but event not processed
    assert resp.status_code == 200
    assert resp.json()["processed"] is False


@pytest.mark.asyncio
async def test_missing_signature_rejected(client: AsyncClient) -> None:
    body, _ = make_signed_event()
    resp = await client.post(
        "/webhooks/payments",
        content=body,
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["processed"] is False


@pytest.mark.asyncio
async def test_duplicate_event_idempotent(client: AsyncClient) -> None:
    body, sig = make_signed_event(event_id="evt_dedup")
    headers = {
        "X-Webhook-Signature": sig,
        "Content-Type": "application/json",
    }
    resp1 = await client.post("/webhooks/payments", content=body, headers=headers)
    resp2 = await client.post("/webhooks/payments", content=body, headers=headers)
    assert resp1.json()["processed"] is True
    assert resp2.json()["processed"] is False
    assert resp2.json()["reason"] == "duplicate"


@pytest.mark.asyncio
async def test_malformed_payload_handled(client: AsyncClient) -> None:
    bad_body = b"not json at all"
    sig = compute_signature(bad_body, WEBHOOK_SECRET)
    resp = await client.post(
        "/webhooks/payments",
        content=bad_body,
        headers={
            "X-Webhook-Signature": sig,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["processed"] is False


@pytest.mark.asyncio
async def test_unknown_event_type_ignored(client: AsyncClient) -> None:
    body, sig = make_signed_event(
        event_id="evt_unknown", event_type="unknown.event"
    )
    resp = await client.post(
        "/webhooks/payments",
        content=body,
        headers={
            "X-Webhook-Signature": sig,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["processed"] is False
    assert resp.json()["reason"] == "unknown_event_type"


@pytest.mark.asyncio
async def test_payment_status_updated(client: AsyncClient) -> None:
    body, sig = make_signed_event(
        event_id="evt_capture",
        event_type="payment.captured",
        payment_id="pay_456",
    )
    resp = await client.post(
        "/webhooks/payments",
        content=body,
        headers={
            "X-Webhook-Signature": sig,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["processed"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_type",
    ["payment.authorized", "payment.captured", "payment.failed", "payment.refunded"],
)
async def test_parametrized_event_types(
    client: AsyncClient, event_type: str
) -> None:
    body, sig = make_signed_event(
        event_id=f"evt_{event_type.replace('.', '_')}",
        event_type=event_type,
    )
    resp = await client.post(
        "/webhooks/payments",
        content=body,
        headers={
            "X-Webhook-Signature": sig,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["processed"] is True
