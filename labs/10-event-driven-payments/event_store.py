"""Append-only event store for payment events."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from models import Event


class EventStore:
    def __init__(self) -> None:
        self._events: list[Event] = []
        self._versions: dict[str, int] = {}

    def append(
        self, aggregate_id: str, event_type: str, data: dict[str, Any]
    ) -> Event:
        """Append an event. Returns the created event."""
        version = self._versions.get(aggregate_id, 0) + 1
        event = Event(
            id=uuid4(),
            aggregate_id=aggregate_id,
            event_type=event_type,
            data=data,
            timestamp=datetime.now(UTC),
            version=version,
        )
        self._events.append(event)
        self._versions[aggregate_id] = version
        return event

    def get_events(self, aggregate_id: str) -> list[Event]:
        """Get all events for an aggregate, ordered by version."""
        return [e for e in self._events if e.aggregate_id == aggregate_id]

    def all_events(self) -> list[Event]:
        """Get all events in the store."""
        return list(self._events)
