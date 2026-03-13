"""Test fixtures for idempotent payments lab."""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def db_path(tmp_path) -> str:
    """Create a temporary database path."""
    return str(tmp_path / "test_payments.sqlite3")


@pytest.fixture
async def app(db_path: str):
    """Create a FastAPI app instance with a test database."""
    # Set env before import so app picks it up
    os.environ["DATABASE_PATH"] = db_path

    from app import app as fastapi_app
    from db import init_db

    await init_db(db_path)
    return fastapi_app


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
