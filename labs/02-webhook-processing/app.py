"""Payment webhook processing endpoint.

POST /webhooks/payments — Receives payment events from a provider.
Verifies HMAC signature, deduplicates events, processes status updates.
Always returns 200 (never leak internal errors to providers).
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from crypto import verify_signature
from db import init_db, is_event_processed, mark_event_processed, update_payment_status
from fastapi import FastAPI, Request
from models import WebhookEvent

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("DATABASE_PATH", "webhooks.sqlite3")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "default_secret")

KNOWN_EVENT_TYPES = {
    "payment.authorized",
    "payment.captured",
    "payment.failed",
    "payment.refunded",
}

STATUS_MAP = {
    "payment.authorized": "AUTHORIZED",
    "payment.captured": "CAPTURED",
    "payment.failed": "FAILED",
    "payment.refunded": "REFUNDED",
}


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    await init_db(DB_PATH)
    yield


app = FastAPI(title="Webhook Processing Lab", lifespan=lifespan)


@app.post("/webhooks/payments")
async def receive_webhook(request: Request) -> dict:
    body = await request.body()
    signature = request.headers.get("X-Webhook-Signature")

    # Always return 200 — never leak info to external callers
    if signature is None:
        logger.warning("Webhook received without signature")
        return {"processed": False, "reason": "missing_signature"}

    if not verify_signature(body, signature, WEBHOOK_SECRET):
        logger.warning("Webhook signature verification failed")
        return {"processed": False, "reason": "invalid_signature"}

    # Parse payload
    try:
        payload = json.loads(body)
        event = WebhookEvent(**payload)
    except (json.JSONDecodeError, Exception) as e:
        logger.error("Failed to parse webhook payload: %s", e)
        return {"processed": False, "reason": "malformed_payload"}

    # Check for unknown event types
    if event.type not in KNOWN_EVENT_TYPES:
        logger.info("Unknown event type: %s", event.type)
        return {"processed": False, "reason": "unknown_event_type"}

    # Deduplicate
    if await is_event_processed(DB_PATH, event.event_id):
        logger.info("Duplicate event: %s", event.event_id)
        return {"processed": False, "reason": "duplicate"}

    # Process the event
    new_status = STATUS_MAP[event.type]
    await update_payment_status(DB_PATH, event.payment_id, new_status)
    await mark_event_processed(DB_PATH, event.event_id)

    logger.info(
        "Webhook processed",
        extra={
            "event_id": event.event_id,
            "event_type": event.type,
            "payment_id": event.payment_id,
        },
    )
    return {"processed": True}
