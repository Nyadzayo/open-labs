"""Test fixtures for webhook processing lab."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from test_helpers import WEBHOOK_SECRET


@pytest.fixture
async def db_path(tmp_path: Any) -> str:
    return str(tmp_path / "test_webhooks.sqlite3")


@pytest.fixture
async def app(db_path: str) -> Any:
    os.environ["DATABASE_PATH"] = db_path
    os.environ["WEBHOOK_SECRET"] = WEBHOOK_SECRET

    from app import app as fastapi_app
    from db import init_db

    await init_db(db_path)
    return fastapi_app


@pytest.fixture
async def client(app: Any) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
