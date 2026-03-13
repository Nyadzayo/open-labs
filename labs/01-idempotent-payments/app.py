"""Idempotent payment creation endpoint.

POST /payments — Creates a payment. Requires Idempotency-Key header.
If the key was seen before, returns the cached response (200).
If the key is new, creates the payment and caches the response (201).
"""

from __future__ import annotations

import logging
import os

from db import DuplicateKeyError, create_payment, get_cached_response, init_db
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from models import PaymentRequest

logger = logging.getLogger(__name__)

app = FastAPI(title="Idempotent Payments Lab")

DB_PATH = os.environ.get("DATABASE_PATH", "payments.sqlite3")


@app.on_event("startup")
async def startup() -> None:
    await init_db(DB_PATH)


@app.post("/payments", status_code=201)
async def create_payment_endpoint(
    payment: PaymentRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> JSONResponse:
    if idempotency_key is None:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header is required",
        )

    # Check for cached response
    cached = await get_cached_response(DB_PATH, idempotency_key)
    if cached is not None:
        logger.info(
            "Idempotency cache hit",
            extra={"idempotency_key": idempotency_key},
        )
        return JSONResponse(content=cached, status_code=200)

    # Create new payment
    try:
        response = await create_payment(
            db_path=DB_PATH,
            idempotency_key=idempotency_key,
            amount=payment.amount,
            currency=payment.currency,
            recipient=payment.recipient,
        )
    except DuplicateKeyError:
        # Concurrent request won the race; return whatever was stored
        cached = await get_cached_response(DB_PATH, idempotency_key)
        if cached is not None:
            return JSONResponse(content=cached, status_code=200)
        # Should never happen, but guard defensively
        raise HTTPException(  # noqa: B904
            status_code=500,
            detail="Idempotency key race unresolvable",
        )
    logger.info(
        "Payment created",
        extra={
            "payment_id": response["id"],
            "idempotency_key": idempotency_key,
            "amount": str(payment.amount),
        },
    )
    return JSONResponse(content=response, status_code=201)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
