# labs/06-retry-patterns/ — Retry Patterns & Circuit Breakers

**Purpose:** Resilient external API calls with exponential backoff and failure isolation.

## Depends on
- Nothing (standalone lab)

## Key files
- resilient_client.py: ResilientClient with retry + circuit breaker
- test_resilient_client.py: 6 tests with respx mocks
- lab.py: marimo notebook — retry and circuit breaker first principles

## Key classes
- `ResilientClient`: httpx wrapper with retry + circuit breaker
- `CircuitState`: CLOSED/OPEN/HALF_OPEN enum
- `CircuitOpenError`: raised when circuit is open

## Test
`pytest labs/06-retry-patterns/ -v`
