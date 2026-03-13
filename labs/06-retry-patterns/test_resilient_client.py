"""Tests for resilient client with retry and circuit breaker."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import httpx
import pytest
import respx
from resilient_client import CircuitOpenError, CircuitState, ResilientClient

BASE_URL = "https://api.provider.test"


@pytest.fixture
async def client() -> AsyncGenerator[ResilientClient, None]:
    c = ResilientClient(
        BASE_URL,
        max_retries=2,
        base_delay=0.01,
        failure_threshold=2,
        recovery_timeout=0.1,
    )
    yield c
    await c.close()


@respx.mock
@pytest.mark.asyncio
async def test_successful_request(client: ResilientClient) -> None:
    respx.get(f"{BASE_URL}/status").respond(200, json={"ok": True})
    resp = await client.request("GET", "/status")
    assert resp.status_code == 200


@respx.mock
@pytest.mark.asyncio
async def test_retry_on_500(client: ResilientClient) -> None:
    route = respx.get(f"{BASE_URL}/pay").mock(
        side_effect=[
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    resp = await client.request("GET", "/pay")
    assert resp.status_code == 200
    assert route.call_count == 3


@respx.mock
@pytest.mark.asyncio
async def test_no_retry_on_400(client: ResilientClient) -> None:
    route = respx.get(f"{BASE_URL}/pay").respond(400)
    resp = await client.request("GET", "/pay")
    assert resp.status_code == 400
    assert route.call_count == 1


@respx.mock
@pytest.mark.asyncio
async def test_circuit_opens_after_threshold(client: ResilientClient) -> None:
    respx.get(f"{BASE_URL}/pay").respond(500)
    for _ in range(2):
        with pytest.raises(httpx.HTTPStatusError):
            await client.request("GET", "/pay")
    assert client.circuit_state == CircuitState.OPEN


@respx.mock
@pytest.mark.asyncio
async def test_circuit_open_rejects(client: ResilientClient) -> None:
    respx.get(f"{BASE_URL}/pay").respond(500)
    for _ in range(2):
        with pytest.raises(httpx.HTTPStatusError):
            await client.request("GET", "/pay")
    with pytest.raises(CircuitOpenError):
        await client.request("GET", "/pay")


@respx.mock
@pytest.mark.asyncio
async def test_circuit_half_open_recovery(client: ResilientClient) -> None:
    call_count = 0

    def side_effect(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count <= 6:  # First 6 calls fail (2 failures * 3 attempts each)
            return httpx.Response(500)
        return httpx.Response(200, json={"ok": True})

    respx.get(f"{BASE_URL}/pay").mock(side_effect=side_effect)
    # Trip the circuit
    for _ in range(2):
        with pytest.raises(httpx.HTTPStatusError):
            await client.request("GET", "/pay")
    assert client.circuit_state == CircuitState.OPEN
    # Wait for recovery timeout
    await asyncio.sleep(0.15)
    # Half-open probe succeeds
    resp = await client.request("GET", "/pay")
    assert resp.status_code == 200
    assert client.circuit_state == CircuitState.CLOSED
