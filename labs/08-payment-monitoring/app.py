"""Payment service with Prometheus metrics."""

from __future__ import annotations

import time

from fastapi import FastAPI, Request, Response
from metrics import PAYMENT_CREATED, PAYMENT_LATENCY
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

app = FastAPI(title="Payment Service (Monitored)")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next: object) -> Response:
    """Record request latency for payment endpoints."""
    start = time.monotonic()
    response = await call_next(request)  # type: ignore[operator]
    if request.url.path.startswith("/payments"):
        duration = time.monotonic() - start
        PAYMENT_LATENCY.observe(duration)
    return response  # type: ignore[return-value]


@app.post("/payments")
async def create_payment() -> dict[str, str]:
    """Create a payment and record metrics."""
    PAYMENT_CREATED.labels(status="PENDING", currency="USD").inc()
    return {"status": "created", "id": "pay_001"}


@app.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
