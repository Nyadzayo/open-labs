"""Fake payment provider API."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Fake Payment Provider")

_charges: dict[str, dict] = {}


@app.post("/v1/charges")
async def create_charge(
    amount: Decimal,
    currency: str,
    source: str,
    description: str | None = None,
) -> JSONResponse:
    charge_id = f"ch_{uuid.uuid4().hex[:12]}"
    charge = {
        "id": charge_id,
        "amount": str(amount),
        "currency": currency,
        "status": "succeeded",
        "created_at": datetime.now(UTC).isoformat(),
    }
    _charges[charge_id] = charge
    return JSONResponse(content=charge, status_code=201)


@app.post("/v1/refunds")
async def create_refund(charge_id: str, amount: Decimal) -> JSONResponse:
    refund = {
        "id": f"rf_{uuid.uuid4().hex[:12]}",
        "charge_id": charge_id,
        "amount": str(amount),
        "status": "pending",
    }
    return JSONResponse(content=refund, status_code=201)
