"""Shared pytest helpers for fintech labs.

Note: asyncio_mode = "auto" in pyproject.toml handles event loop
management — no need for a custom event_loop fixture.
"""

from __future__ import annotations

from typing import Any

from httpx import ASGITransport, AsyncClient


def create_test_client(app: Any) -> AsyncClient:
    """Create an httpx async test client for a FastAPI app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
