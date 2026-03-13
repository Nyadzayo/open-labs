"""Pydantic models for webhook events."""

from __future__ import annotations

from pydantic import BaseModel


class WebhookEvent(BaseModel):
    event_id: str
    type: str
    payment_id: str
    data: dict | None = None
