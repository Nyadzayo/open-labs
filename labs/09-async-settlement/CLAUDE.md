# labs/09-async-settlement/ — Async Settlement Processing

**Purpose:** Demonstrate async payment settlement with retry, idempotency, and dead-letter queue patterns.

## Depends on
- Nothing (standalone lab, concepts from Celery implemented in pure Python)

## Key files
- settlement.py: SettlementProcessor with queue, retry, DLQ
- models.py: PaymentStatus, SettlementResult enums
- test_settlement.py: 9 tests covering happy path, retry, DLQ, idempotency
- lab.py: marimo notebook — async processing first principles

## Test
`pytest labs/09-async-settlement/ -v`
