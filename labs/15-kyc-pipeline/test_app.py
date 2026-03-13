"""Integration tests for KYC pipeline API."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def db_path(tmp_path: Any) -> str:
    return str(tmp_path / "test_kyc.sqlite3")


@pytest.fixture
async def app(db_path: str) -> Any:
    os.environ["DATABASE_PATH"] = db_path
    from app import app as fastapi_app
    from db import init_db
    await init_db(db_path)
    return fastapi_app


@pytest.fixture
async def client(app: Any) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_upload_valid_document(client: AsyncClient) -> None:
    resp = await client.post("/documents", json={
        "customer_id": "cust_001",
        "filename": "passport.pdf",
        "content_type": "application/pdf",
        "size_bytes": 5000,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "APPROVED"
    assert "id" in data


@pytest.mark.asyncio
async def test_upload_invalid_type_rejected(client: AsyncClient) -> None:
    resp = await client.post("/documents", json={
        "customer_id": "cust_001",
        "filename": "virus.exe",
        "content_type": "application/exe",
        "size_bytes": 1024,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert "rejection_reason" in data


@pytest.mark.asyncio
async def test_get_document_status(client: AsyncClient) -> None:
    resp = await client.post("/documents", json={
        "customer_id": "cust_001",
        "filename": "id.jpg",
        "content_type": "image/jpeg",
        "size_bytes": 2048,
    })
    doc_id = resp.json()["id"]

    resp = await client.get(f"/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_document_not_found(client: AsyncClient) -> None:
    resp = await client.get("/documents/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
