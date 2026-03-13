# Lab 04: Ledger Invariants

## Role Relevance
Financial Backend Engineer — every fintech with money movement needs balanced ledgers.

## Business Problem
Without double-entry bookkeeping, money can appear or disappear from the system. Single-entry ledgers drift silently. A payment goes out but the fee isn't recorded. A refund credits the customer but doesn't debit the merchant.

## Failure Mode
Single-entry system: merchant gets paid $100, platform records revenue, but nobody records the debit. End of month: books don't balance, nobody knows where $100K went.

## First Principles
Every movement of money has exactly two sides: where it came from (credit) and where it went (debit). The sum of all entries across all accounts must always equal zero.

## How to Test
```bash
pytest labs/04-ledger-invariants/ -v
```

## Edge Cases Covered
- Zero and negative amounts rejected
- Self-transfer (same account debit and credit)
- Decimal precision (0.01 + 0.02 = 0.03, not 0.030000000000000004)
- Multiple transactions accumulate correctly
- Empty ledger invariant holds

## What This Proves
"Built double-entry ledger with database-enforced invariants proving zero-sum balance across all accounts."
