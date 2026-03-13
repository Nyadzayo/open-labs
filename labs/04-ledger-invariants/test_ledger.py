"""Tests for double-entry ledger invariants."""

from __future__ import annotations

from decimal import Decimal

import pytest
from ledger import InvariantViolationError, Ledger


@pytest.fixture
def ledger() -> Ledger:
    return Ledger()


def test_record_transaction_creates_balanced_pair(ledger: Ledger) -> None:
    tx_id = ledger.record_transaction("wallet", "merchant", Decimal("100.00"))
    entries = ledger.transaction_entries(tx_id)
    assert len(entries) == 2
    assert sum(e.amount for e in entries) == Decimal("0")


def test_debit_account_balance_increases(ledger: Ledger) -> None:
    ledger.record_transaction("wallet", "merchant", Decimal("50.00"))
    assert ledger.balance("wallet") == Decimal("50.00")


def test_credit_account_balance_decreases(ledger: Ledger) -> None:
    ledger.record_transaction("wallet", "merchant", Decimal("50.00"))
    assert ledger.balance("merchant") == Decimal("-50.00")


def test_multiple_transactions_accumulate(ledger: Ledger) -> None:
    ledger.record_transaction("wallet", "merchant_a", Decimal("30.00"))
    ledger.record_transaction("wallet", "merchant_b", Decimal("20.00"))
    assert ledger.balance("wallet") == Decimal("50.00")


def test_invariant_holds_after_transactions(ledger: Ledger) -> None:
    ledger.record_transaction("wallet", "merchant", Decimal("100.00"))
    ledger.record_transaction("fees", "platform", Decimal("2.50"))
    assert ledger.verify_invariant()


def test_empty_ledger_invariant(ledger: Ledger) -> None:
    assert ledger.verify_invariant()


def test_zero_amount_rejected(ledger: Ledger) -> None:
    with pytest.raises(InvariantViolationError, match="positive"):
        ledger.record_transaction("a", "b", Decimal("0"))


def test_negative_amount_rejected(ledger: Ledger) -> None:
    with pytest.raises(InvariantViolationError, match="positive"):
        ledger.record_transaction("a", "b", Decimal("-10.00"))


def test_same_account_debit_credit(ledger: Ledger) -> None:
    """Self-transfer still balances."""
    ledger.record_transaction("wallet", "wallet", Decimal("100.00"))
    assert ledger.balance("wallet") == Decimal("0")
    assert ledger.verify_invariant()


def test_precision_preserved(ledger: Ledger) -> None:
    ledger.record_transaction("a", "b", Decimal("0.01"))
    ledger.record_transaction("a", "b", Decimal("0.02"))
    assert ledger.balance("a") == Decimal("0.03")
    assert ledger.verify_invariant()
