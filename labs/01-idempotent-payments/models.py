"""Pydantic models for the idempotent payments lab."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    recipient: str = Field(min_length=1)


class PaymentResponse(BaseModel):
    id: UUID
    status: str
    amount: Decimal
    currency: str
    recipient: str
    created_at: datetime
