"""SQLite persistence for KYC documents."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import aiosqlite

DB_PATH = "kyc.sqlite3"


async def init_db(db_path: str = DB_PATH) -> None:
    """Create documents table."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'UPLOADED',
                rejection_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def create_document(
    db_path: str,
    customer_id: str,
    filename: str,
    content_type: str,
    size_bytes: int,
) -> dict[str, Any]:
    """Create a new document record."""
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    now = datetime.now(UTC).isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """INSERT INTO documents
               (id, customer_id, filename, content_type,
                size_bytes, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'UPLOADED', ?, ?)""",
            (doc_id, customer_id, filename, content_type, size_bytes, now, now),
        )
        await db.commit()
    return {
        "id": doc_id,
        "customer_id": customer_id,
        "filename": filename,
        "status": "UPLOADED",
        "created_at": now,
    }


async def get_document(db_path: str, doc_id: str) -> dict[str, Any] | None:
    """Get document by ID."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


async def update_document_status(
    db_path: str, doc_id: str, status: str, reason: str | None = None
) -> bool:
    """Update document status. Returns True if document found."""
    now = datetime.now(UTC).isoformat()
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            """UPDATE documents SET status = ?, rejection_reason = ?, updated_at = ?
               WHERE id = ?""",
            (status, reason, now, doc_id),
        )
        await db.commit()
        return cursor.rowcount > 0
