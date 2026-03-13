# Lab 01: Idempotent Payment Creation

## Role Relevance
Backend Engineer — Payments at any fintech. This is the most commonly asked payments concept in interviews.

## Business Problem
When a customer clicks "Pay" twice, or a retry mechanism resends a request, the payment must not be created twice. Double-charging destroys customer trust and costs money to reverse.

## Failure Mode
Without idempotency: duplicate network requests create duplicate payments. The customer is charged twice. Reversals are manual, slow, and error-prone.

## First Principles
Every payment request carries a unique idempotency key. Before creating a payment, check if the key exists. If it does, return the cached response. If it doesn't, create the payment and cache the response atomically.

## Architecture
```
Client --[POST /payments + Idempotency-Key]--> FastAPI
  --> Check idempotency_keys table
    --> Found? Return cached response (200)
    --> Not found? Create payment + store key (201)
  --> SQLite (MVP) / PostgreSQL (production)
```

## How to Run
```bash
cd labs/01-idempotent-payments
uvicorn app:app --reload

# Create a payment
curl -X POST http://localhost:8000/payments \
  -H "Idempotency-Key: abc-123" \
  -H "Content-Type: application/json" \
  -d '{"amount": "50.00", "currency": "USD", "recipient": "merchant_42"}'
```

## How to Test
```bash
pytest labs/01-idempotent-payments/ -v
```

## Edge Cases Covered
- Duplicate request returns cached response
- Missing idempotency key rejected (400)
- Different body with same key returns cached (Stripe approach)
- Concurrent duplicate requests (SQLite: eventually consistent; Postgres: SELECT FOR UPDATE)
- Invalid amounts rejected (422)

## What This Proves
"Built idempotent payment endpoint with SQLite persistence, proving duplicate-safe payment creation with 8 pytest edge-case scenarios."
