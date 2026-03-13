"""Async settlement processor with retry and dead-letter queue."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models import PaymentStatus, SettlementResult


class PermanentFailureError(Exception):
    """Non-retryable settlement failure."""


class MaxRetriesExceededError(Exception):
    """Task exceeded retry limit."""


@dataclass
class Payment:
    id: str
    amount: str
    status: PaymentStatus = PaymentStatus.CAPTURED


@dataclass
class SettlementTask:
    payment_id: str
    attempts: int = 0
    max_retries: int = 3


@dataclass
class SettlementProcessor:
    """Simulates async settlement with retry and DLQ."""

    payments: dict[str, Payment] = field(default_factory=dict)
    queue: list[SettlementTask] = field(default_factory=list)
    dlq: list[SettlementTask] = field(default_factory=list)
    settled: list[str] = field(default_factory=list)
    _settle_fn: Any = None

    def set_settle_fn(self, fn: Any) -> None:
        """Set the settlement function (for testing with fakes)."""
        self._settle_fn = fn

    def enqueue(self, payment_id: str) -> SettlementTask:
        """Add a payment to the settlement queue."""
        task = SettlementTask(payment_id=payment_id)
        self.queue.append(task)
        return task

    def process_next(self) -> str:
        """Process next task from queue. Returns result description."""
        if not self.queue:
            return "queue_empty"

        task = self.queue.pop(0)
        payment = self.payments.get(task.payment_id)

        if payment is None:
            return "payment_not_found"

        # Idempotency: already settled
        if payment.status == PaymentStatus.SETTLED:
            return "already_settled"

        # Must be in CAPTURED state to settle
        if payment.status != PaymentStatus.CAPTURED:
            self.dlq.append(task)
            return "invalid_state_to_dlq"

        task.attempts += 1
        payment.status = PaymentStatus.SETTLING

        try:
            result = self._do_settle(payment)
            if result == SettlementResult.SUCCESS:
                payment.status = PaymentStatus.SETTLED
                self.settled.append(payment.id)
                return "settled"
            elif result == SettlementResult.TRANSIENT_FAILURE:
                if task.attempts >= task.max_retries:
                    payment.status = PaymentStatus.FAILED
                    self.dlq.append(task)
                    return "max_retries_to_dlq"
                payment.status = PaymentStatus.CAPTURED
                self.queue.append(task)  # Re-enqueue for retry
                return "retrying"
            else:  # PERMANENT_FAILURE
                payment.status = PaymentStatus.FAILED
                self.dlq.append(task)
                return "permanent_failure_to_dlq"
        except Exception:
            payment.status = PaymentStatus.CAPTURED
            if task.attempts >= task.max_retries:
                payment.status = PaymentStatus.FAILED
                self.dlq.append(task)
                return "exception_to_dlq"
            self.queue.append(task)
            return "exception_retrying"

    def _do_settle(self, payment: Payment) -> SettlementResult:
        """Call settlement provider. Override with set_settle_fn for testing."""
        if self._settle_fn:
            return self._settle_fn(payment)
        return SettlementResult.SUCCESS
