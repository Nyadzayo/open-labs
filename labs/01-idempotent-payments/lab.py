import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    # Lab 01: Idempotent Payment Creation

    ## Why does this exist?

    When a customer clicks "Pay" and their browser hangs, they click again.
    When a mobile app retries a failed network request, it sends the same payment twice.
    When a webhook delivery system retries on timeout, it triggers the same charge.

    **Without idempotency:** The customer gets charged twice. You lose trust and money.

    **With idempotency:** Every payment request carries a unique key. If we've seen
    that key before, we return the cached result instead of creating a duplicate.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## First Principles

    Idempotency means: **doing something twice has the same effect as doing it once.**

    The core mechanism is simple:
    1. Client sends a request with a unique key
    2. Server checks: "Have I seen this key before?"
    3. If yes → return the cached response
    4. If no → process the request, cache the response, return it
    """)
    return


@app.cell
def _():
    # The smallest idempotent system — a dict
    store = {}

    def create_payment(key: str, amount: float) -> dict:
        if key in store:
            return store[key]  # Cache hit — return existing
        payment = {"id": f"pay_{len(store)+1}", "amount": amount, "status": "PENDING"}
        store[key] = payment
        return payment

    # First call — creates payment
    result1 = create_payment("key-abc", 50.00)
    # Second call — returns cached
    result2 = create_payment("key-abc", 50.00)

    print(f"First call:  {result1}")
    print(f"Second call: {result2}")
    print(f"Same object? {result1['id'] == result2['id']}")
    return create_payment, result1, result2, store


@app.cell
def _(mo):
    mo.md("""
    ## What breaks without it?

    Let's remove the idempotency check and see what happens.
    """)
    return


@app.cell
def _():
    # WITHOUT idempotency — broken version
    broken_store = []

    def broken_create_payment(amount: float) -> dict:
        payment = {"id": f"pay_{len(broken_store)+1}", "amount": amount}
        broken_store.append(payment)
        return payment

    # Customer clicks "Pay" twice
    r1 = broken_create_payment(50.00)
    r2 = broken_create_payment(50.00)

    print(f"Payment 1: {r1}")
    print(f"Payment 2: {r2}")
    print(f"Customer charged ${r1['amount'] + r2['amount']:.2f} instead of ${r1['amount']:.2f}")
    print(f"DOUBLE CHARGE!")
    return broken_create_payment, broken_store, r1, r2


@app.cell
def _(mo):
    mo.md("""
    ## Edge Cases

    1. **Missing key** — Reject with 400. Never create a payment without an idempotency key.
    2. **Same key, different body** — Two approaches:
       - **Stripe approach:** Return cached response (key is authoritative)
       - **Strict approach:** Return 409/422 (body mismatch is an error)
       We use the Stripe approach. The key IS the identity of the request.
    3. **Concurrent duplicates** — Two requests with the same key arrive at the same time.
       With SQLite, this is eventually consistent. With PostgreSQL, use `SELECT FOR UPDATE`
       to ensure only one request wins the race.
    4. **Key expiry** — Should keys expire? Yes, typically after 24-48 hours.
       Keeps the table from growing forever. Extension task.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## From Dict to Database

    The dict version works but doesn't survive restarts.
    The production version uses a database table:

    ```sql
    CREATE TABLE idempotency_keys (
        key TEXT PRIMARY KEY,
        response_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    ```

    The payment creation and key storage happen in a **single transaction**:
    - Insert payment → Insert idempotency key → Commit
    - If anything fails, both roll back → No orphan records

    See `app.py` for the FastAPI implementation and `db.py` for the database layer.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Reflection

    - What surprised you about this concept?
    - What happens if the DB crashes between creating the payment and storing the key?
    - Could you explain idempotency in a 2-minute interview answer?

    **Confidence score:** Rate yourself 1-5 on this concept and log it in PROGRESS.md
    """)
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
