# Lab 03: Payment State Machine

## Role Relevance
Payments Backend, Fintech System Design. Understanding payment lifecycles is fundamental.

## Business Problem
Payments go through a lifecycle: PENDING -> AUTHORIZED -> CAPTURED -> SETTLED. Without enforcement, a bug could transition a PENDING payment directly to REFUNDED, corrupting your ledger.

## Architecture
```
PENDING -> AUTHORIZED -> CAPTURED -> SETTLED
   |          |    \         |
   v          v     v        v
CANCELLED  FAILED CANCELLED REFUNDED
```

## How to Test
```bash
pytest labs/03-payment-state-machine/ -v
```

## Edge Cases Covered
- All 7 valid transitions
- 12 invalid transitions (skipping states, backwards, from terminal)
- Full happy path (PENDING -> SETTLED)
- Refund path (CAPTURED -> REFUNDED)
- Cancellation from different states

## What This Proves
"Designed payment state machine enforcing 6-state lifecycle with 100% transition coverage."
