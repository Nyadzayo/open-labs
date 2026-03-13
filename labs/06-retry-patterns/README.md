# Lab 06: Retry Patterns & Circuit Breakers

## Role Relevance
Integration Engineer / Platform Engineer — every payment provider integration needs resilient HTTP calls.

## Business Problem
Payment provider returns 500. Without retry: payment lost. Without backoff: you DDoS the provider. Without circuit breaker: one failing provider takes down your entire system.

## Failure Mode
Provider outage → every request retries aggressively → provider stays down → your queue fills up → customer-facing timeouts → revenue loss.

## First Principles
- **Retry with backoff**: Try again, but wait longer each time (exponential)
- **Circuit breaker**: After N failures, stop trying for a while (protect both sides)
- **Don't retry 4xx**: Client errors won't fix themselves

## How to Test
```bash
pytest labs/06-retry-patterns/ -v
```

## Edge Cases Covered
- 200 success (no retry)
- 500 with retry succeeding on 3rd attempt
- 400 returns immediately (no retry)
- Circuit opens after threshold failures
- Open circuit rejects immediately
- Half-open recovery after timeout

## What This Proves
"Implemented circuit breaker with exponential backoff for payment provider integration."
