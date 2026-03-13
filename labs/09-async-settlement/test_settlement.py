"""Tests for async settlement processing."""

from __future__ import annotations

import pytest
from models import PaymentStatus, SettlementResult
from settlement import Payment, SettlementProcessor


@pytest.fixture
def processor() -> SettlementProcessor:
    p = SettlementProcessor()
    return p


def _make_payment(processor: SettlementProcessor, pid: str = "pay_001") -> Payment:
    payment = Payment(id=pid, amount="100.00")
    processor.payments[pid] = payment
    return payment


def test_successful_settlement(processor: SettlementProcessor) -> None:
    _make_payment(processor)
    processor.enqueue("pay_001")
    result = processor.process_next()
    assert result == "settled"
    assert processor.payments["pay_001"].status == PaymentStatus.SETTLED
    assert "pay_001" in processor.settled


def test_idempotent_already_settled(processor: SettlementProcessor) -> None:
    payment = _make_payment(processor)
    payment.status = PaymentStatus.SETTLED
    processor.enqueue("pay_001")
    result = processor.process_next()
    assert result == "already_settled"


def test_invalid_state_goes_to_dlq(processor: SettlementProcessor) -> None:
    payment = _make_payment(processor)
    payment.status = PaymentStatus.PENDING
    processor.enqueue("pay_001")
    result = processor.process_next()
    assert result == "invalid_state_to_dlq"
    assert len(processor.dlq) == 1


def test_transient_failure_retries(processor: SettlementProcessor) -> None:
    _make_payment(processor)
    call_count = 0

    def failing_settle(_: Payment) -> SettlementResult:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return SettlementResult.TRANSIENT_FAILURE
        return SettlementResult.SUCCESS

    processor.set_settle_fn(failing_settle)
    processor.enqueue("pay_001")

    # First two attempts: transient failure → retry
    assert processor.process_next() == "retrying"
    assert processor.process_next() == "retrying"
    # Third attempt: success
    assert processor.process_next() == "settled"
    assert processor.payments["pay_001"].status == PaymentStatus.SETTLED


def test_max_retries_to_dlq(processor: SettlementProcessor) -> None:
    _make_payment(processor)
    processor.set_settle_fn(lambda _: SettlementResult.TRANSIENT_FAILURE)
    processor.enqueue("pay_001")

    for _ in range(3):
        processor.process_next()

    assert processor.payments["pay_001"].status == PaymentStatus.FAILED
    assert len(processor.dlq) == 1


def test_permanent_failure_to_dlq(processor: SettlementProcessor) -> None:
    _make_payment(processor)
    processor.set_settle_fn(lambda _: SettlementResult.PERMANENT_FAILURE)
    processor.enqueue("pay_001")
    result = processor.process_next()
    assert result == "permanent_failure_to_dlq"
    assert len(processor.dlq) == 1
    assert processor.payments["pay_001"].status == PaymentStatus.FAILED


def test_payment_not_found(processor: SettlementProcessor) -> None:
    processor.enqueue("nonexistent")
    result = processor.process_next()
    assert result == "payment_not_found"


def test_empty_queue(processor: SettlementProcessor) -> None:
    result = processor.process_next()
    assert result == "queue_empty"


def test_multiple_payments_settle(processor: SettlementProcessor) -> None:
    for i in range(3):
        _make_payment(processor, f"pay_{i}")
        processor.enqueue(f"pay_{i}")

    for _ in range(3):
        processor.process_next()

    assert len(processor.settled) == 3
    for i in range(3):
        assert processor.payments[f"pay_{i}"].status == PaymentStatus.SETTLED
