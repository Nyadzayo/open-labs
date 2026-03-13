"""Test fixtures for webhook processing lab."""

from __future__ import annotations

import sys
from pathlib import Path

# Collection-time isolation: clear cached modules from other labs
_lab_dir = str(Path(__file__).parent)
_shared = {
    "app", "db", "models", "crypto", "test_helpers", "state_machine",
    "ledger", "reconciler", "resilient_client", "metrics",
    "event_store", "read_model", "producer", "consumer",
    "provider", "client", "schemas", "rate_limiter",
    "rule_engine", "pipeline", "settlement",
}
for _name in list(sys.modules):
    if _name in _shared:
        del sys.modules[_name]
if _lab_dir in sys.path:
    sys.path.remove(_lab_dir)
sys.path.insert(0, _lab_dir)

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
