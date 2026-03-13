"""Event models for payment event sourcing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class Event:
    id: UUID
    aggregate_id: str
    event_type: str
    data: dict[str, Any]
    timestamp: datetime
    version: int
