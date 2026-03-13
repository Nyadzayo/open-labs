"""Tests for K8s payment service health probes."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def app() -> Any:
    import app as app_module
    from app import app as fastapi_app
    app_module._ready = True
    return fastapi_app


@pytest.fixture
async def client(app: Any) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_liveness_returns_alive(client: AsyncClient) -> None:
    resp = await client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_returns_ready(client: AsyncClient) -> None:
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["ready"] is True


@pytest.mark.asyncio
async def test_readiness_not_ready() -> None:
    """Before startup, readiness should return 503."""
    import app as app_module
    original = app_module._ready
    app_module._ready = False
    try:
        from app import app as fastapi_app
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/health/ready")
            assert resp.status_code == 503
            assert resp.json()["ready"] is False
    finally:
        app_module._ready = original


@pytest.mark.asyncio
async def test_create_payment(client: AsyncClient) -> None:
    resp = await client.post("/payments")
    assert resp.status_code == 200
    assert resp.json()["status"] == "created"


@pytest.mark.asyncio
async def test_root_returns_uptime(client: AsyncClient) -> None:
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "payment-api"
    assert "uptime_seconds" in data
