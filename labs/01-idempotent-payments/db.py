"""SQLite persistence for the idempotent payments lab.

MVP uses SQLite for simplicity. Production variant would use
PostgreSQL with SELECT FOR UPDATE for concurrent dedup.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import aiosqlite

DB_PATH = "payments.sqlite3"


async def init_db(db_path: str = DB_PATH) -> None:
    """Create tables if they don't exist."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'PENDING',
                amount TEXT NOT NULL,
                currency TEXT NOT NULL,
                recipient TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                key TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def get_cached_response(
    db_path: str, idempotency_key: str
) -> dict[str, Any] | None:
    """Look up a cached response by idempotency key."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT response_json FROM idempotency_keys WHERE key = ?",
            (idempotency_key,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return json.loads(row[0])  # type: ignore[no-any-return]


class DuplicateKeyError(Exception):
    """Raised when an idempotency key already exists (concurrent race)."""


async def create_payment(
    db_path: str,
    idempotency_key: str,
    amount: Decimal,
    currency: str,
    recipient: str,
) -> dict[str, Any]:
    """Create a payment and store the idempotency key atomically.

    Raises DuplicateKeyError if the idempotency key was concurrently inserted.
    Callers should handle this by fetching the cached response.
    """
    payment_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    response: dict[str, Any] = {
        "id": payment_id,
        "status": "PENDING",
        "amount": str(amount),
        "currency": currency,
        "recipient": recipient,
        "created_at": now,
    }
    insert_payments = (
        "INSERT INTO payments"
        " (id, status, amount, currency, recipient, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?)"
    )
    insert_keys = (
        "INSERT INTO idempotency_keys (key, response_json, created_at)"
        " VALUES (?, ?, ?)"
    )
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                insert_payments,
                (payment_id, "PENDING", str(amount), currency, recipient, now),
            )
            await db.execute(
                insert_keys,
                (idempotency_key, json.dumps(response), now),
            )
            await db.commit()
    except sqlite3.IntegrityError as exc:
        if "idempotency_keys" in str(exc) or "UNIQUE" in str(exc):
            raise DuplicateKeyError(idempotency_key) from exc
        raise
    return response
