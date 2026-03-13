# labs/01-idempotent-payments/ — Idempotent Payments

**Purpose:** Prevent duplicate payment creation via idempotency keys with SQLite (MVP) / PostgreSQL (production).

## Depends on
- [shared/CLAUDE.md](../../shared/CLAUDE.md) — conftest fixtures

## Key files
- lab.py: marimo notebook — first principles exploration of idempotency
- app.py: FastAPI app with POST /payments endpoint
- db.py: SQLite persistence with idempotency key lookup/insert
- models.py: PaymentRequest, PaymentResponse Pydantic models
- test_app.py: 8 tests including concurrent duplicate detection

## Key functions
- create_payment(): Atomic payment creation with idempotency check
- get_cached_response(): Lookup by idempotency key

## Integration points
- SQLite (payments + idempotency_keys tables)
- Feeds into Lab 07 (K8s deployment) and Lab 08 (monitoring)

## Test
`pytest labs/01-idempotent-payments/ -v`
