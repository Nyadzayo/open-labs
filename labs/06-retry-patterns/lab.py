import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    # Lab 06: Retry Patterns & Circuit Breakers

    ## Why does resilience matter?

    Your payment service calls an external provider to authorise a charge.
    The provider returns a 500. What happens next?

    - **No retry:** The payment is lost. The customer sees an error. Revenue is gone.
    - **Immediate retry (no backoff):** You hammer the provider at full speed while
      it is already struggling. You become the cause of the outage that is taking you down.
    - **Retry without a circuit breaker:** Every request in your queue retries
      repeatedly. Your thread pool fills up. Your database connection pool exhausts.
      One external failure cascades into a full system outage.

    **The correct answer:** Retry with exponential backoff, stop retrying once you
    know the provider is down, and probe carefully before resuming.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## First Principles — Exponential Backoff

    If a provider fails, the most likely cause is transient load. Retrying immediately
    adds more load. Waiting briefly gives the provider time to recover.

    The formula: `delay = base_delay * (2 ** attempt)`

    | Attempt | Delay (base=0.1s) |
    |---------|-------------------|
    | 0       | 0.1s              |
    | 1       | 0.2s              |
    | 2       | 0.4s              |
    | 3       | 0.8s              |

    Each retry doubles the wait. After 3 retries you have waited 1.5 seconds total —
    enough for most transient failures to clear. After 10 retries you are waiting
    over a minute per attempt — at that point, use a circuit breaker instead.

    **Critical distinction:** Only retry on 5xx (server errors). Never retry on 4xx
    (client errors). A 400 Bad Request will not become a 200 by being sent again.
    """)
    return


@app.cell
def _():
    # Backoff math — smallest working example
    base_delay = 0.1
    max_retries = 3

    print("Exponential backoff schedule:")
    total = 0.0
    for attempt in range(max_retries):
        delay = base_delay * (2**attempt)
        total += delay
        print(f"  attempt {attempt + 1}: wait {delay:.2f}s  (cumulative: {total:.2f}s)")

    print(f"\nTotal wait before giving up: {total:.2f}s")
    return


@app.cell
def _(mo):
    mo.md("""
    ## Circuit Breaker States

    The circuit breaker is a state machine with three states:

    ```
    CLOSED ──(N failures)──► OPEN ──(timeout elapsed)──► HALF_OPEN
       ▲                                                       │
       └────────────────(success)──────────────────────────────┘
    ```

    **CLOSED (normal operation)**
    Requests pass through. Failures are counted. When the failure count reaches
    `failure_threshold`, the circuit opens.

    **OPEN (fast fail)**
    All requests are rejected immediately with `CircuitOpenError`. No network calls
    are made. The provider gets breathing room to recover. Your system fails fast
    instead of queuing up slow timeouts.

    **HALF_OPEN (probe)**
    After `recovery_timeout` seconds, the circuit transitions to HALF_OPEN.
    The next request is allowed through as a probe. If it succeeds, the circuit
    closes and normal operation resumes. If it fails, the circuit reopens.

    This is the key insight: **protect both sides**. The circuit breaker protects
    your system from slow failures, and protects the provider from being bombarded
    while it is trying to recover.
    """)
    return


@app.cell
def _():
    # Simulate the circuit breaker state machine — no network needed
    import time

    class SimpleCircuit:
        CLOSED = "CLOSED"
        OPEN = "OPEN"
        HALF_OPEN = "HALF_OPEN"

        def __init__(self, threshold: int = 2, timeout: float = 1.0) -> None:
            self.state = self.CLOSED
            self.failures = 0
            self.threshold = threshold
            self.timeout = timeout
            self._opened_at: float | None = None

        def record_failure(self) -> None:
            self.failures += 1
            self._opened_at = time.monotonic()
            if self.failures >= self.threshold:
                self.state = self.OPEN
                print(f"  → circuit OPENED after {self.failures} failures")

        def record_success(self) -> None:
            self.failures = 0
            self.state = self.CLOSED
            print("  → circuit CLOSED (success)")

        def allow_request(self) -> bool:
            if self.state == self.CLOSED:
                return True
            if self.state == self.OPEN:
                if self._opened_at and (time.monotonic() - self._opened_at) >= self.timeout:
                    self.state = self.HALF_OPEN
                    print("  → circuit moved to HALF_OPEN (probing)")
                    return True
                return False
            # HALF_OPEN: allow one probe
            return True

    circuit = SimpleCircuit(threshold=2, timeout=0.1)

    print("=== Simulating circuit breaker lifecycle ===")
    print(f"Initial state: {circuit.state}")

    print("\n[Failures accumulate]")
    circuit.record_failure()
    print(f"State: {circuit.state}")
    circuit.record_failure()
    print(f"State: {circuit.state}")

    print("\n[Request rejected while OPEN]")
    allowed = circuit.allow_request()
    print(f"Request allowed: {allowed}")

    print("\n[Wait for recovery timeout]")
    time.sleep(0.15)
    allowed = circuit.allow_request()
    print(f"Request allowed after timeout: {allowed}  (state: {circuit.state})")

    print("\n[Probe succeeds]")
    circuit.record_success()
    print(f"Final state: {circuit.state}")
    return


@app.cell
def _(mo):
    mo.md("""
    ## What breaks without these patterns?

    **No retry — lost payment**

    ```
    Client → POST /pay → Provider (500) → Error returned to client
    ```

    The provider was briefly overloaded. Retrying once would have succeeded.
    Instead, the customer's payment fails. They try again manually. You get a
    duplicate if your idempotency key handling is wrong. You lose the sale if
    they give up.

    **No circuit breaker — cascade failure**

    ```
    Provider down (30s)
    → 1000 requests queued, each retrying 3x with 10s backoff
    → 30s * 1000 requests = 30,000 seconds of thread time held
    → Thread pool exhausted
    → All other endpoints timeout
    → Full system outage caused by one failing dependency
    ```

    The circuit breaker cuts this off at the source. After 3 failures it stops
    sending requests entirely. Threads are freed. Other payment methods still work.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Edge Cases

    **4xx vs 5xx**

    | Status | Meaning | Retry? |
    |--------|---------|--------|
    | 400 Bad Request | Your request is wrong | No — it won't fix itself |
    | 401 Unauthorized | Auth problem | No — need new credentials |
    | 404 Not Found | Resource missing | No — it won't appear |
    | 429 Too Many Requests | Rate limited | Yes, but with longer backoff |
    | 500 Internal Server Error | Provider bug/overload | Yes |
    | 502 Bad Gateway | Upstream failure | Yes |
    | 503 Service Unavailable | Provider down | Yes — primary circuit breaker trigger |
    | 504 Gateway Timeout | Timeout at proxy | Yes |

    **Timeout vs Connection Error**

    A `ConnectError` means the provider is unreachable (DNS failure, network partition).
    A `TimeoutException` means the provider accepted the request but didn't respond in time.
    Both are retriable — but a timeout means the request *may have been processed*,
    which is why idempotency keys (Lab 01) are essential alongside retry logic.

    **Jitter**

    In production, add random jitter to the backoff delay: `delay * (0.5 + random())`.
    Without jitter, all clients that hit the same error at the same time will retry
    at exactly the same moment, creating a thundering herd that re-triggers the failure.
    """)
    return


@app.cell
def _():
    # Edge case: demonstrate why 4xx should not be retried
    import random

    def simulate_call(status_code: int, attempt: int) -> str:
        if status_code == 400:
            return f"attempt {attempt}: 400 Bad Request — not retrying (client error)"
        if status_code >= 500:
            if attempt < 2:
                return f"attempt {attempt}: {status_code} — retrying..."
            return f"attempt {attempt}: {status_code} — giving up after {attempt + 1} attempts"
        return f"attempt {attempt}: {status_code} OK"

    print("=== 400 Bad Request (should not retry) ===")
    print(simulate_call(400, 0))

    print("\n=== 500 Internal Server Error (should retry) ===")
    for i in range(3):
        print(simulate_call(500, i))

    print("\n=== Backoff with jitter ===")
    base = 0.1
    for attempt in range(4):
        jitter = random.uniform(0.5, 1.5)
        delay = base * (2**attempt) * jitter
        print(f"  attempt {attempt}: delay ≈ {delay:.3f}s")
    return


@app.cell
def _(mo):
    mo.md("""
    ## Reflection

    The `ResilientClient` in this lab wraps any HTTP call with:

    1. **Retry loop** — up to `max_retries` attempts on 5xx or network errors
    2. **Exponential backoff** — each retry waits `base_delay * 2^attempt`
    3. **Circuit breaker** — opens after `failure_threshold` exhausted attempts
    4. **Fast fail** — open circuit raises `CircuitOpenError` immediately
    5. **Recovery probe** — after `recovery_timeout`, allows one request through

    The implementation is 70 lines. Every payment service integration should wrap
    external HTTP calls this way before shipping.

    **What to say in an interview:**

    > "We wrapped every external provider call in a circuit breaker with exponential
    > backoff. On 5xx we retry up to 3 times with doubling delays. After 3 consecutive
    > failures we open the circuit for 5 seconds to protect the provider and free our
    > thread pool. We never retry 4xx — those are client errors that won't self-heal.
    > We use idempotency keys on all payment requests so retries are safe."

    ---

    **Confidence score:** 9/10

    The implementation is clean and the tests cover all six behaviour cases. The one
    thing missing from a production system is jitter on the backoff delay to prevent
    thundering herd — straightforward to add as `base_delay * (2**attempt) * random.uniform(0.5, 1.5)`.
    """)
    return


@app.cell
def _(mo):
    return (mo,)


if __name__ == "__main__":
    app.run()
