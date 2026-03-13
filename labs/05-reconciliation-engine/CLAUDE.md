# labs/05-reconciliation-engine/ — Reconciliation Engine

**Purpose:** Detect mismatches between internal ledger and provider settlement data.

## Depends on
- Nothing (standalone lab)

## Key files
- reconciler.py: reconcile() function with Record, Mismatch, MismatchType
- test_reconciler.py: 8 tests covering all 4 mismatch types
- lab.py: marimo notebook — reconciliation first principles

## Key functions
- `reconcile(internal, provider)`: Compare record lists, return mismatches

## Test
`pytest labs/05-reconciliation-engine/ -v`
