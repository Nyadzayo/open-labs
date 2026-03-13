"""Tests for reconciliation engine."""

from __future__ import annotations

from decimal import Decimal

from reconciler import MismatchType, Record, reconcile


def _r(tx_id: str, amount: str = "100.00", status: str = "SETTLED") -> Record:
    return Record(tx_id, Decimal(amount), status)


def test_perfect_match() -> None:
    internal = [_r("tx_1"), _r("tx_2")]
    provider = [_r("tx_1"), _r("tx_2")]
    assert reconcile(internal, provider) == []


def test_missing_internal() -> None:
    result = reconcile([], [_r("tx_1")])
    assert len(result) == 1
    assert result[0].mismatch_type == MismatchType.MISSING_INTERNAL


def test_missing_provider() -> None:
    result = reconcile([_r("tx_1")], [])
    assert len(result) == 1
    assert result[0].mismatch_type == MismatchType.MISSING_PROVIDER


def test_amount_mismatch() -> None:
    result = reconcile([_r("tx_1", "100.00")], [_r("tx_1", "99.99")])
    assert result[0].mismatch_type == MismatchType.AMOUNT_MISMATCH
    assert result[0].internal_value == "100.00"
    assert result[0].provider_value == "99.99"


def test_status_mismatch() -> None:
    result = reconcile(
        [_r("tx_1", status="CAPTURED")],
        [_r("tx_1", status="SETTLED")],
    )
    assert result[0].mismatch_type == MismatchType.STATUS_MISMATCH
    assert result[0].internal_value == "CAPTURED"
    assert result[0].provider_value == "SETTLED"


def test_multiple_mismatches() -> None:
    internal = [_r("tx_1"), _r("tx_3", "50.00")]
    provider = [_r("tx_2"), _r("tx_3", "55.00")]
    result = reconcile(internal, provider)
    types = {m.mismatch_type for m in result}
    assert MismatchType.MISSING_PROVIDER in types
    assert MismatchType.MISSING_INTERNAL in types
    assert MismatchType.AMOUNT_MISMATCH in types


def test_empty_both_sides() -> None:
    assert reconcile([], []) == []


def test_both_amount_and_status_mismatch() -> None:
    result = reconcile(
        [_r("tx_1", "100.00", "CAPTURED")],
        [_r("tx_1", "99.00", "SETTLED")],
    )
    assert len(result) == 2
    types = {m.mismatch_type for m in result}
    assert MismatchType.AMOUNT_MISMATCH in types
    assert MismatchType.STATUS_MISMATCH in types
