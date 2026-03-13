# Lab 09: Async Settlement Processing

## Role Relevance
Payments Backend — settlement is inherently async. Every fintech processes settlements in background workers.

## Business Problem
Customer pays → payment captured instantly → settlement with bank takes 1-3 days. This must happen reliably in the background. If the settlement task fails, it must retry. If it keeps failing, it goes to a dead-letter queue for human review.

## First Principles
- **Enqueue**: Captured payment creates a settlement task
- **Process**: Worker picks up task, calls settlement provider
- **Retry**: Transient failures retry with backoff (up to max_retries)
- **DLQ**: Permanent failures or exhausted retries go to dead-letter queue
- **Idempotent**: Same task processed twice doesn't double-settle

## How to Test
```bash
pytest labs/09-async-settlement/ -v
```

## Edge Cases Covered
- Successful settlement
- Already-settled idempotency
- Invalid state rejected to DLQ
- Transient failure retries (succeeds on 3rd attempt)
- Max retries exceeded → DLQ
- Permanent failure → DLQ immediately
- Payment not found
- Empty queue
- Multiple payments settle correctly

## What This Proves
"Built async settlement pipeline implementing dead-letter queues and idempotent task processing."
