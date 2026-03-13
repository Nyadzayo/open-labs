import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    # Lab 02: Payment Webhook Processing

    ## Why does this exist?

    Payment providers (Stripe, Adyen, PayPal) notify your system about payment
    status changes by sending HTTP POST requests called **webhooks**.

    Problem 1: Anyone can send a POST to your webhook URL. How do you know it's
    really from your provider? **HMAC signature verification.**

    Problem 2: Providers retry on timeout. The same event may arrive 2-3 times.
    How do you avoid processing it twice? **Event deduplication.**

    Problem 3: Your server crashes while processing. The provider sees a timeout
    and retries. You must **always return 200** — even on internal errors — to
    avoid infinite retry loops.
    """)
    return


@app.cell
def _():
    import hashlib
    import hmac

    # HMAC from first principles
    secret = b"my_webhook_secret"
    message = b'{"event_id": "evt_001", "type": "payment.captured"}'

    # Generate signature
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
    print(f"Message:   {message.decode()}")
    print(f"Signature: {signature}")

    # Verify — correct
    is_valid = hmac.compare_digest(
        signature,
        hmac.new(secret, message, hashlib.sha256).hexdigest()
    )
    print(f"\nValid signature? {is_valid}")

    # Verify — tampered message
    tampered = b'{"event_id": "evt_001", "type": "payment.refunded"}'
    is_valid_tampered = hmac.compare_digest(
        signature,
        hmac.new(secret, tampered, hashlib.sha256).hexdigest()
    )
    print(f"Tampered valid?  {is_valid_tampered}")
    return hashlib, hmac, is_valid, is_valid_tampered, message, secret, signature, tampered


@app.cell
def _(mo):
    mo.md("""
    ## Why `hmac.compare_digest` and not `==`?

    String comparison with `==` is **not constant-time**. It returns `False` as soon
    as it finds the first different character. An attacker can measure response times
    to guess the signature one character at a time (**timing attack**).

    `hmac.compare_digest` always compares the full string, taking the same time
    regardless of where differences are. This is a **code review checkpoint** —
    always verify you're using `compare_digest` in webhook verification code.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Deduplication

    Providers send the same event multiple times. Your `processed_events` table
    tracks which event IDs you've already handled:

    ```
    Event arrives → Check processed_events → Already there? Skip. → New? Process + mark.
    ```

    ## Always Return 200

    Never return 4xx/5xx to a webhook provider. They will retry, causing a storm.
    Log the error internally, return 200, and investigate later.

    See `app.py` for the production implementation.

    ## Reflection
    - Why return 200 even on internal errors?
    - What if the provider stops sending webhooks entirely?
    - How would you handle webhook secret key rotation?
    """)
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
