# Lab 02: Payment Webhook Processing

## Role Relevance
Integration Engineer, Payments Backend. Every fintech receives webhooks from Stripe, Adyen, PayPal, banks.

## Business Problem
Payment providers send webhook events to notify you of status changes. Without verification, anyone can POST fake events. Without deduplication, the same event processed twice corrupts your state.

## Failure Mode
Without signature verification: attackers send fake "payment.captured" events. Without deduplication: provider retries cause double-processing.

## Architecture
```
Provider --[POST + X-Webhook-Signature]--> FastAPI
  --> Verify HMAC-SHA256 signature
  --> Check processed_events table
  --> Parse event, update payment status
  --> Always return 200
```

## How to Test
```bash
pytest labs/02-webhook-processing/ -v
```

## Edge Cases Covered
- Valid/invalid/missing signatures
- Duplicate event delivery (idempotent)
- Malformed JSON payload
- Unknown event types
- Parametrized across 4 payment event types

## What This Proves
"Implemented webhook receiver with HMAC-SHA256 signature verification and idempotent event processing, tested against replay and duplicate delivery attacks."
