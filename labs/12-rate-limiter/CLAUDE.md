# labs/12-rate-limiter/ — Token Bucket Rate Limiter

**Purpose:** Protect payment endpoints from abuse with per-key rate limiting.

## Depends on
- Nothing (standalone lab)

## Key files
- rate_limiter.py: RateLimiter class with token bucket algorithm
- test_rate_limiter.py: 8 tests covering limits, refill, per-key isolation

## Test
`pytest labs/12-rate-limiter/ -v`
