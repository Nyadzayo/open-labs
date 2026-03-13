# labs/02-webhook-processing/ — Webhook Processing

**Purpose:** Receive, verify, and deduplicate payment webhook events using HMAC-SHA256.

## Depends on
- [shared/CLAUDE.md](../../shared/CLAUDE.md) — conftest fixtures

## Key files
- lab.py: marimo notebook — HMAC from scratch, verification demos
- app.py: FastAPI webhook receiver endpoint
- crypto.py: HMAC-SHA256 signature verification
- db.py: Event dedup table and payment status updates
- test_crypto.py: 5 signature verification unit tests
- test_app.py: 9 integration tests with parametrized event types

## Key functions
- verify_signature(): Constant-time HMAC comparison
- is_event_processed(): Deduplication check
- receive_webhook(): Main webhook handler

## Integration points
- SQLite (processed_events + payments tables)

## Test
`pytest labs/02-webhook-processing/ -v`
