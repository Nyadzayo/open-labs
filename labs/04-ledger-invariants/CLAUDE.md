# labs/04-ledger-invariants/ — Double-Entry Ledger

**Purpose:** Prove that every financial transaction creates balanced debit+credit pairs with zero-sum invariant.

## Depends on
- Nothing (standalone Tier 1 lab)

## Key files
- ledger.py: Ledger class with record_transaction, balance, verify_invariant
- test_ledger.py: 10 tests covering invariants, edge cases, precision
- lab.py: marimo notebook — first principles of double-entry bookkeeping

## Key functions
- `Ledger.record_transaction(debit, credit, amount)`: Atomic balanced pair
- `Ledger.balance(account)`: Account sum
- `Ledger.verify_invariant()`: Global zero-sum check

## Test
`pytest labs/04-ledger-invariants/ -v`
