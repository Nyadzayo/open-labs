"""Double-entry ledger with balance invariants."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass
class LedgerEntry:
    id: UUID
    account: str
    amount: Decimal  # positive = debit, negative = credit
    transaction_id: UUID


class InvariantViolationError(Exception):
    """Raised when a ledger operation would violate invariants."""


class Ledger:
    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    def record_transaction(
        self, debit_account: str, credit_account: str, amount: Decimal
    ) -> UUID:
        """Record a balanced debit+credit pair. Returns transaction_id."""
        if amount <= 0:
            raise InvariantViolationError("Amount must be positive")
        tx_id = uuid4()
        self._entries.append(
            LedgerEntry(
                id=uuid4(), account=debit_account, amount=amount, transaction_id=tx_id
            )
        )
        self._entries.append(
            LedgerEntry(
                id=uuid4(), account=credit_account, amount=-amount, transaction_id=tx_id
            )
        )
        return tx_id

    def balance(self, account: str) -> Decimal:
        """Sum of all entries for an account."""
        return sum(
            (e.amount for e in self._entries if e.account == account),
            Decimal("0"),
        )

    def verify_invariant(self) -> bool:
        """Sum of ALL entries across ALL accounts must be zero."""
        total = sum((e.amount for e in self._entries), Decimal("0"))
        return total == Decimal("0")

    def transaction_entries(self, tx_id: UUID) -> list[LedgerEntry]:
        """Get entries for a transaction — must always be exactly 2."""
        return [e for e in self._entries if e.transaction_id == tx_id]
