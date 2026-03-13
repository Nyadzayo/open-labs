# Lab 05: Reconciliation Engine

## Role Relevance
Payments Operations / Financial Backend — uniquely fintech. Generic engineers can't speak to reconciliation.

## Business Problem
Internal records say payment tx_123 was $100. Provider settlement says it was $99.50. Without reconciliation, this $0.50 discrepancy per transaction accumulates silently.

## Failure Mode
End-of-month close: books don't balance. Nobody knows which transactions drifted. Manual investigation of thousands of records. Revenue recognition delayed.

## First Principles
Two systems independently track the same transactions. Reconciliation joins them on transaction ID and flags disagreements: missing records, amount drift, status disagreement.

## How to Test
```bash
pytest labs/05-reconciliation-engine/ -v
```

## Edge Cases Covered
- Perfect match (no mismatches)
- Missing on internal side
- Missing on provider side
- Amount mismatch with values preserved
- Status mismatch
- Multiple simultaneous mismatches
- Both amount and status wrong on same transaction
- Empty datasets

## What This Proves
"Built reconciliation engine detecting 4 mismatch types between internal ledger and provider settlements."
