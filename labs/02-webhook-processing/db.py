"""SQLite persistence for webhook event deduplication."""

from __future__ import annotations

from datetime import UTC

import aiosqlite

DB_PATH = "webhooks.sqlite3"


async def init_db(db_path: str = DB_PATH) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS processed_events (
                event_id TEXT PRIMARY KEY,
                processed_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'PENDING'
            )
        """)
        await db.commit()


async def is_event_processed(db_path: str, event_id: str) -> bool:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT 1 FROM processed_events WHERE event_id = ?",
            (event_id,),
        )
        return await cursor.fetchone() is not None


async def mark_event_processed(db_path: str, event_id: str) -> None:
    from datetime import datetime

    async with aiosqlite.connect(db_path) as db:
        sql = (
            "INSERT OR IGNORE INTO processed_events"
            " (event_id, processed_at) VALUES (?, ?)"
        )
        await db.execute(sql, (event_id, datetime.now(UTC).isoformat()))
        await db.commit()


async def update_payment_status(
    db_path: str, payment_id: str, new_status: str
) -> None:
    async with aiosqlite.connect(db_path) as db:
        sql = (
            "INSERT INTO payments (id, status) VALUES (?, ?)"
            " ON CONFLICT(id) DO UPDATE SET status = ?"
        )
        await db.execute(sql, (payment_id, new_status, new_status))
        await db.commit()
