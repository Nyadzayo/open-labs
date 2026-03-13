"""Payment service with Kubernetes health probes."""

from __future__ import annotations

import time

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Payment Service (K8s)")

_start_time = time.monotonic()
_ready = False


@app.on_event("startup")
async def startup() -> None:
    global _ready  # noqa: PLW0603
    _ready = True


@app.get("/health/live")
async def liveness() -> dict[str, str]:
    """Liveness probe: is the process alive?"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness() -> JSONResponse:
    """Readiness probe: can the service handle traffic?"""
    if not _ready:
        return JSONResponse(
            content={"status": "not_ready", "ready": False},
            status_code=503,
        )
    return JSONResponse(content={"status": "ready", "ready": True})


@app.post("/payments")
async def create_payment() -> dict[str, str]:
    """Stub payment endpoint for K8s demo."""
    return {"status": "created", "message": "Payment processed"}


@app.get("/")
async def root() -> dict[str, str]:
    uptime = round(time.monotonic() - _start_time, 1)
    return {"service": "payment-api", "uptime_seconds": str(uptime)}
