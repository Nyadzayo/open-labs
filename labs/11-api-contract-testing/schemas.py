"""API contract schemas for payment provider."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ChargeRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    source: str
    description: str | None = None


class ChargeResponse(BaseModel):
    id: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime


class RefundRequest(BaseModel):
    charge_id: str
    amount: Decimal = Field(gt=0)


class RefundResponse(BaseModel):
    id: str
    charge_id: str
    amount: Decimal
    status: str
