"""Tests for monitored payment service."""

from __future__ import annotations

import contextlib
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def app() -> Any:
    # Reset prometheus metrics between tests — unregister all payment/webhook collectors
    from prometheus_client import REGISTRY

    # Collect unique collector objects (not names) to avoid double-unregister
    seen: set[int] = set()
    collectors_to_remove = []
    for name in list(REGISTRY._names_to_collectors.keys()):
        if name.startswith(("payment_", "webhook_")):
            col = REGISTRY._names_to_collectors[name]
            if id(col) not in seen:
                seen.add(id(col))
                collectors_to_remove.append(col)

    for collector in collectors_to_remove:
        with contextlib.suppress(Exception):
            REGISTRY.unregister(collector)

    # Re-import to re-register metrics
    import sys

    # Remove cached modules so reload picks up fresh state
    for mod_name in ("metrics", "app"):
        sys.modules.pop(mod_name, None)

    import app as app_module  # noqa: F401
    import metrics  # noqa: F401 — side-effect: registers metrics

    return app_module.app


@pytest.fixture
async def client(app: Any) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_metrics_endpoint_exists(client: AsyncClient) -> None:
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    content_type = resp.headers.get("content-type", "")
    assert "text/plain" in content_type


@pytest.mark.asyncio
async def test_payment_counter_increments(client: AsyncClient) -> None:
    await client.post("/payments")
    await client.post("/payments")
    resp = await client.get("/metrics")
    body = resp.text
    assert "payment_created_total" in body


@pytest.mark.asyncio
async def test_payment_latency_recorded(client: AsyncClient) -> None:
    await client.post("/payments")
    resp = await client.get("/metrics")
    body = resp.text
    assert "payment_latency_seconds" in body


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_payment_returns_id(client: AsyncClient) -> None:
    resp = await client.post("/payments")
    assert resp.status_code == 200
    assert "id" in resp.json()
