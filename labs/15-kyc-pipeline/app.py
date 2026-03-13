"""KYC document pipeline API."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from db import create_document, get_document, init_db, update_document_status
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from models import DocumentState
from pipeline import validate_document
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("DATABASE_PATH", "kyc.sqlite3")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    await init_db(DB_PATH)
    yield


app = FastAPI(title="KYC Document Pipeline", lifespan=lifespan)


class UploadRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    content_type: str
    size_bytes: int = Field(gt=0)


@app.post("/documents", status_code=201)
async def upload_document(req: UploadRequest) -> JSONResponse:
    """Upload a KYC document for validation."""
    doc = await create_document(
        DB_PATH, req.customer_id, req.filename, req.content_type, req.size_bytes
    )

    # Start validation immediately
    validation = validate_document(req.filename, req.content_type, req.size_bytes)

    # Transition to VALIDATING
    await update_document_status(DB_PATH, doc["id"], DocumentState.VALIDATING)

    if validation.valid:
        await update_document_status(DB_PATH, doc["id"], DocumentState.APPROVED)
        doc["status"] = DocumentState.APPROVED
    else:
        await update_document_status(
            DB_PATH, doc["id"], DocumentState.REJECTED, validation.reason
        )
        doc["status"] = DocumentState.REJECTED
        doc["rejection_reason"] = validation.reason

    logger.info("Document %s: %s", doc["id"], doc["status"])
    return JSONResponse(content=doc, status_code=201)


@app.get("/documents/{doc_id}")
async def get_document_status(doc_id: str) -> JSONResponse:
    """Get document status."""
    doc = await get_document(DB_PATH, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return JSONResponse(content=doc)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
