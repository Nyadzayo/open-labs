"""CQRS read model (projection) built from events."""

from __future__ import annotations

from typing import Any

from models import Event


class PaymentReadModel:
    """Projection that builds payment state from events."""

    def __init__(self) -> None:
        self._payments: dict[str, dict[str, Any]] = {}

    def apply(self, event: Event) -> None:
        """Apply a single event to update the read model."""
        pid = event.aggregate_id

        if event.event_type == "PaymentCreated":
            self._payments[pid] = {
                **event.data,
                "status": "PENDING",
                "version": event.version,
            }
        elif event.event_type == "PaymentAuthorized":
            if pid in self._payments:
                self._payments[pid]["status"] = "AUTHORIZED"
                self._payments[pid]["version"] = event.version
        elif event.event_type == "PaymentCaptured":
            if pid in self._payments:
                self._payments[pid]["status"] = "CAPTURED"
                self._payments[pid]["version"] = event.version
        elif event.event_type == "PaymentSettled":
            if pid in self._payments:
                self._payments[pid]["status"] = "SETTLED"
                self._payments[pid]["version"] = event.version
        elif event.event_type == "PaymentRefunded" and pid in self._payments:
            self._payments[pid]["status"] = "REFUNDED"
            self._payments[pid]["version"] = event.version

    def get(self, payment_id: str) -> dict[str, Any] | None:
        """Get current state of a payment."""
        return self._payments.get(payment_id)

    def list_all(self) -> dict[str, dict[str, Any]]:
        """Get all payments."""
        return dict(self._payments)

    def rebuild(self, events: list[Event]) -> None:
        """Rebuild the entire read model from a list of events."""
        self._payments.clear()
        for event in events:
            self.apply(event)
