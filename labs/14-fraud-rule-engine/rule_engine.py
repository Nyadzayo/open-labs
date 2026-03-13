"""Configurable fraud rule engine with pluggable rules."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from models import Decision, RuleResult, Transaction

Rule = Callable[[Transaction, list[Transaction]], RuleResult]


def amount_threshold_rule(
    tx: Transaction,
    _history: list[Transaction],
    threshold: Decimal = Decimal("10000"),
) -> RuleResult:
    """Flag transactions over a threshold amount."""
    if tx.amount > threshold:
        return RuleResult(
            "amount_threshold", 0.8, f"Amount {tx.amount} exceeds {threshold}"
        )
    return RuleResult("amount_threshold", 0.0, "Amount within threshold")


def velocity_rule(
    tx: Transaction,
    history: list[Transaction],
    window: float = 3600,
    max_count: int = 10,
) -> RuleResult:
    """Flag customers with too many transactions in a time window."""
    recent = [
        h
        for h in history
        if h.customer_id == tx.customer_id
        and tx.timestamp - h.timestamp <= window
    ]
    if len(recent) >= max_count:
        return RuleResult(
            "velocity", 0.9, f"{len(recent)} transactions in window"
        )
    return RuleResult("velocity", 0.0, "Velocity within limits")


def country_blocklist_rule(
    tx: Transaction,
    _history: list[Transaction],
    blocked: set[str] | None = None,
) -> RuleResult:
    """Reject transactions from blocked countries."""
    blocked = blocked or {"NK", "IR", "SY"}
    if tx.country in blocked:
        return RuleResult(
            "country_blocklist", 1.0, f"Country {tx.country} is blocked"
        )
    return RuleResult("country_blocklist", 0.0, "Country allowed")


class RuleEngine:
    """Evaluate transactions against configurable rules."""

    def __init__(self, rules: list[Rule] | None = None) -> None:
        if rules is None:
            self._rules: list[Rule] = [
                amount_threshold_rule,
                velocity_rule,
                country_blocklist_rule,
            ]
        else:
            self._rules = rules

    def evaluate(
        self,
        tx: Transaction,
        history: list[Transaction] | None = None,
    ) -> tuple[Decision, list[RuleResult]]:
        """Evaluate all rules, return decision and individual results."""
        history = history or []
        results = [rule(tx, history) for rule in self._rules]
        max_score = max((r.score for r in results), default=0.0)

        if max_score >= 0.9:
            decision = Decision.REJECT
        elif max_score >= 0.5:
            decision = Decision.REVIEW
        else:
            decision = Decision.APPROVE

        return decision, results
