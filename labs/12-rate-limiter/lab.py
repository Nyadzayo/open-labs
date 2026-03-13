"""Lab 12: Token Bucket Rate Limiter — marimo notebook."""

import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # Lab 12: Token Bucket Rate Limiter

        **Role relevance:** Backend Engineer / Platform Engineer — every API needs rate limiting.
        Payment APIs especially.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## 1. WHY Rate Limiting

        Without rate limiting a payment API:

        - A malicious actor sends 10,000 requests/second
        - Your database connection pool saturates
        - Legitimate customers can't complete purchases
        - Revenue stops; chargebacks spike

        With rate limiting:

        - Attacker receives **429 Too Many Requests** after N requests/second
        - Legitimate traffic flows normally inside the limit
        - Database load stays predictable

        Real examples: Stripe enforces per-key limits (100 req/s live, 25 req/s test).
        Plaid, Adyen, and every major payment processor publish their rate limit headers.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## 2. Token Bucket Algorithm

        ```
        Bucket capacity = N tokens
        Refill rate     = R tokens / second

        On each request:
          1. Compute elapsed time since last refill
          2. Add elapsed * R tokens (capped at N)
          3. If tokens >= 1: consume 1, allow request
          4. Else: reject with 429
        ```

        Properties:
        - Allows **bursts** up to N (the bucket fills up when idle)
        - Sustains at most R requests/second over any long window
        - Per-key: each API key / user ID gets its own independent bucket
        """
    )
    return


@app.cell
def _():
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from rate_limiter import RateLimiter
    return RateLimiter, os, sys


@app.cell
def _(RateLimiter, mo):
    mo.md("## 3. Smallest Example — 3 tokens, exhaust, refill")
    limiter_demo = RateLimiter(max_tokens=3, refill_rate=1.0)
    results = []
    for i in range(4):
        allowed = limiter_demo.allow("demo_user")
        results.append(f"Request {i + 1}: {'ALLOWED' if allowed else 'REJECTED (429)'}")
    mo.md("\n".join(f"- {r}" for r in results))
    return allowed, i, limiter_demo, results


@app.cell
def _(mo):
    mo.md(
        """
        After exhausting the 3 tokens the 4th request is immediately rejected.
        At 1 token/second, waiting 1 second would restore 1 token and allow the next request.
        """
    )
    return


@app.cell
def _(RateLimiter, mo):
    mo.md("## 4. Per-Key Isolation")
    iso_limiter = RateLimiter(max_tokens=2, refill_rate=0.0)
    rows = []
    for key in ["alice", "bob", "alice", "bob", "alice"]:
        result = iso_limiter.allow(key)
        rows.append(f"- `{key}`: {'ALLOWED' if result else 'REJECTED'}")
    mo.md(
        "Each key has an independent bucket — alice exhausting her limit does not affect bob.\n\n"
        + "\n".join(rows)
    )
    return iso_limiter, key, result, rows


@app.cell
def _(mo):
    mo.md(
        """
        ## 5. Alternatives

        | Algorithm | Burst | Memory | Smoothness |
        |-----------|-------|--------|------------|
        | **Token bucket** | Yes (up to N) | O(keys) | Bursty |
        | Fixed window | Yes (reset at boundary) | O(keys) | Bursty, edge spike |
        | Sliding window log | No | O(keys * limit) | Smooth |
        | Sliding window counter | Approx | O(keys) | Smooth |
        | Leaky bucket | No | O(keys) | Very smooth (queue drain) |

        Token bucket is the most common choice for payment APIs: it tolerates short
        bursts (checkout spike) while bounding sustained throughput.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## 6. HTTP 429 Too Many Requests

        When a request is rejected the server should respond:

        ```http
        HTTP/1.1 429 Too Many Requests
        Retry-After: 1
        X-RateLimit-Limit: 100
        X-RateLimit-Remaining: 0
        X-RateLimit-Reset: 1710374460
        Content-Type: application/json

        {"error": "rate_limit_exceeded", "retry_after_seconds": 1}
        ```

        Key headers:
        - `Retry-After`: seconds until the client may retry (RFC 7231)
        - `X-RateLimit-Limit`: maximum requests allowed in the window
        - `X-RateLimit-Remaining`: tokens left right now
        - `X-RateLimit-Reset`: Unix timestamp when bucket resets / refills

        Django middleware example:

        ```python
        def payment_view(request):
            key = request.headers.get("X-Api-Key", request.META["REMOTE_ADDR"])
            if not limiter.allow(key):
                return JsonResponse(
                    {"error": "rate_limit_exceeded"},
                    status=429,
                    headers={"Retry-After": "1"},
                )
            ...
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## 7. Reflection

        **What I built:** A pure-Python token bucket rate limiter with per-key buckets,
        burst support capped at `max_tokens`, and time-based refill via `time.monotonic()`.

        **What this proves on a resume:**
        > "Implemented token bucket rate limiter for payment API with per-client limits,
        > burst tolerance, and 429 responses with Retry-After headers."

        **Production delta:** In production this state lives in Redis (`SET NX` + `INCRBY`
        with TTL, or the `redis-py` `TokenBucket` pattern) so multiple API server instances
        share the same counters. The algorithm is identical; only the storage layer changes.

        ---

        **Confidence score (0–10):** How confident are you that you could implement
        this from scratch in an interview?
        """
    )
    return


@app.cell
def _(mo):
    confidence = mo.ui.slider(0, 10, value=7, label="Confidence score")
    return (confidence,)


@app.cell
def _(confidence, mo):
    level = (
        "Solid — you understand the core algorithm and its trade-offs."
        if confidence.value >= 7
        else "Keep practicing — re-read the token bucket section and rewrite from memory."
    )
    mo.md(f"**Score {confidence.value}/10** — {level}")
    return (level,)


if __name__ == "__main__":
    app.run()
