"""Tests for fraud rule engine."""

from __future__ import annotations

from decimal import Decimal

from models import Decision, RuleResult, Transaction
from rule_engine import (
    RuleEngine,
    amount_threshold_rule,
    country_blocklist_rule,
    velocity_rule,
)


def _tx(
    tx_id: str = "tx_001",
    amount: str = "100.00",
    country: str = "US",
    customer_id: str = "cust_001",
    timestamp: float = 1000.0,
) -> Transaction:
    return Transaction(
        id=tx_id,
        amount=Decimal(amount),
        currency="USD",
        country=country,
        customer_id=customer_id,
        timestamp=timestamp,
    )


# Individual rule tests

def test_amount_under_threshold() -> None:
    result = amount_threshold_rule(_tx(amount="5000"), [])
    assert result.score == 0.0


def test_amount_over_threshold() -> None:
    result = amount_threshold_rule(_tx(amount="15000"), [])
    assert result.score == 0.8


def test_amount_at_threshold() -> None:
    result = amount_threshold_rule(_tx(amount="10000"), [])
    assert result.score == 0.0  # Not over, equal


def test_velocity_under_limit() -> None:
    history = [_tx(timestamp=500.0 + i) for i in range(5)]
    result = velocity_rule(_tx(timestamp=1000.0), history)
    assert result.score == 0.0


def test_velocity_over_limit() -> None:
    history = [_tx(timestamp=500.0 + i) for i in range(10)]
    result = velocity_rule(_tx(timestamp=1000.0), history)
    assert result.score == 0.9


def test_velocity_different_customer() -> None:
    """History from other customers doesn't count."""
    history = [_tx(customer_id="other", timestamp=500.0 + i) for i in range(20)]
    result = velocity_rule(_tx(timestamp=1000.0), history)
    assert result.score == 0.0


def test_country_allowed() -> None:
    result = country_blocklist_rule(_tx(country="US"), [])
    assert result.score == 0.0


def test_country_blocked() -> None:
    result = country_blocklist_rule(_tx(country="NK"), [])
    assert result.score == 1.0


# Engine integration tests

def test_engine_approves_normal() -> None:
    engine = RuleEngine()
    decision, results = engine.evaluate(_tx())
    assert decision == Decision.APPROVE
    assert len(results) == 3


def test_engine_reviews_high_amount() -> None:
    engine = RuleEngine()
    decision, _ = engine.evaluate(_tx(amount="15000"))
    assert decision == Decision.REVIEW


def test_engine_rejects_blocked_country() -> None:
    engine = RuleEngine()
    decision, _ = engine.evaluate(_tx(country="IR"))
    assert decision == Decision.REJECT


def test_engine_rejects_velocity() -> None:
    engine = RuleEngine()
    history = [_tx(timestamp=500.0 + i) for i in range(10)]
    decision, _ = engine.evaluate(_tx(timestamp=1000.0), history)
    assert decision == Decision.REJECT


def test_engine_empty_rules() -> None:
    engine = RuleEngine(rules=[])
    decision, results = engine.evaluate(_tx())
    assert decision == Decision.APPROVE
    assert results == []


def test_engine_custom_rule() -> None:
    def always_flag(tx: Transaction, _: list[Transaction]) -> RuleResult:
        return RuleResult("custom", 0.95, "Always flags")

    engine = RuleEngine(rules=[always_flag])
    decision, _ = engine.evaluate(_tx())
    assert decision == Decision.REJECT
