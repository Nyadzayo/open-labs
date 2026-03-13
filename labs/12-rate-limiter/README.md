# Lab 12: Rate Limiter

## Role Relevance
Backend Engineer / Platform Engineer — every API needs rate limiting. Payment APIs especially.

## Business Problem
Malicious actor sends 10,000 payment requests per second. Without rate limiting: your database melts, legitimate customers can't pay. With rate limiting: attacker gets 429, legitimate traffic flows normally.

## First Principles
- **Token bucket**: Each client has a bucket of N tokens, refilled at R tokens/second
- **Request arrives**: Token available? Allow + consume. No token? Reject (429).
- **Per-key**: Each API key/user gets independent limits

## How to Test
```bash
pytest labs/12-rate-limiter/ -v
```

## Edge Cases Covered
- Under limit: allowed
- Over limit: rejected
- Independent per key
- Tokens refill over time
- Max tokens cap (doesn't over-fill)
- Burst + refill cycle
- Zero refill rate = permanent depletion
- Remaining count accurate

## What This Proves
"Implemented Redis-backed token bucket rate limiter for payment API with per-client limits."
