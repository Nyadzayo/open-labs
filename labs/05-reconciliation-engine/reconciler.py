"""Reconciliation engine: detect mismatches between internal and provider records."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class MismatchType(StrEnum):
    MISSING_INTERNAL = "MISSING_INTERNAL"
    MISSING_PROVIDER = "MISSING_PROVIDER"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    STATUS_MISMATCH = "STATUS_MISMATCH"


@dataclass(frozen=True)
class Record:
    transaction_id: str
    amount: Decimal
    status: str


@dataclass(frozen=True)
class Mismatch:
    transaction_id: str
    mismatch_type: MismatchType
    internal_value: str | None = None
    provider_value: str | None = None


def reconcile(
    internal: list[Record], provider: list[Record]
) -> list[Mismatch]:
    """Compare internal vs provider records, return all mismatches."""
    mismatches: list[Mismatch] = []
    internal_map = {r.transaction_id: r for r in internal}
    provider_map = {r.transaction_id: r for r in provider}

    all_ids = set(internal_map) | set(provider_map)

    for tx_id in sorted(all_ids):
        i_rec = internal_map.get(tx_id)
        p_rec = provider_map.get(tx_id)

        if i_rec is None:
            mismatches.append(Mismatch(tx_id, MismatchType.MISSING_INTERNAL))
            continue
        if p_rec is None:
            mismatches.append(Mismatch(tx_id, MismatchType.MISSING_PROVIDER))
            continue
        if i_rec.amount != p_rec.amount:
            mismatches.append(Mismatch(
                tx_id, MismatchType.AMOUNT_MISMATCH,
                str(i_rec.amount), str(p_rec.amount),
            ))
        if i_rec.status != p_rec.status:
            mismatches.append(Mismatch(
                tx_id, MismatchType.STATUS_MISMATCH,
                i_rec.status, p_rec.status,
            ))

    return mismatches
