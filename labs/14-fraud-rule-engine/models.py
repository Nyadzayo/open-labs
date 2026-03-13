"""Models for fraud rule engine."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class Decision(StrEnum):
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


@dataclass(frozen=True)
class Transaction:
    id: str
    amount: Decimal
    currency: str
    country: str
    customer_id: str
    timestamp: float


@dataclass(frozen=True)
class RuleResult:
    rule_name: str
    score: float  # 0.0 = no risk, 1.0 = max risk
    reason: str
