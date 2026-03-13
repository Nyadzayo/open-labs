import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    # Lab 04: Ledger Invariants

    ## Why does this exist?

    Without double-entry bookkeeping, money can appear or disappear from your system.

    Single-entry ledgers drift silently: a payment goes out but the fee isn't recorded.
    A refund credits the customer but nobody debits the merchant. End of month —
    books don't balance and nobody knows where $100K went.

    **The fix:** every movement of money has exactly two sides.
    Where it came from (credit) and where it went (debit).
    The sum of all entries across all accounts must always equal zero.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## First Principles

    Double-entry bookkeeping dates to 15th-century Venice. The insight:

    ```
    A payment of $100 from wallet to merchant creates TWO entries:
      wallet   +100  (debit — the wallet gave money)
      merchant -100  (credit — the merchant received money)

    Sum: +100 + (-100) = 0
    ```

    This is not just accounting convention. It's a **mathematical invariant**:
    the global sum across every account must always be zero, always.
    If it isn't, money was created or destroyed — a bug.
    """)
    return


@app.cell
def _():
    # Smallest example: build the ledger and record a transaction
    from decimal import Decimal

    from ledger import Ledger

    ledger = Ledger()
    tx_id = ledger.record_transaction("wallet", "merchant", Decimal("100.00"))

    entries = ledger.transaction_entries(tx_id)
    for e in entries:
        print(f"  account={e.account:12s}  amount={e.amount:>10}")

    print(f"\nwallet balance:   {ledger.balance('wallet')}")
    print(f"merchant balance: {ledger.balance('merchant')}")
    print(f"invariant holds:  {ledger.verify_invariant()}")
    return Decimal, Ledger, entries, ledger, tx_id


@app.cell
def _(mo):
    mo.md("""
    ## Break It — Single-Entry System

    What if we only recorded the debit side?
    """)
    return


@app.cell
def _(Decimal):
    # Single-entry: only record who paid, not who received
    single_entry: list[dict] = []

    def record_single(account: str, amount: Decimal) -> None:
        single_entry.append({"account": account, "amount": amount})

    record_single("wallet", Decimal("100.00"))   # wallet gave money — recorded
    # merchant received — NOT recorded
    record_single("wallet", Decimal("50.00"))    # another payment
    # another merchant — NOT recorded

    total = sum(e["amount"] for e in single_entry)
    print(f"Single-entry total: {total}")
    print("This is NOT zero — balance has drifted. Money appeared from nowhere.")
    return record_single, single_entry, total


@app.cell
def _(mo):
    mo.md("""
    ## Fix It — Double-Entry Restores the Invariant
    """)
    return


@app.cell
def _(Decimal, Ledger):
    fixed_ledger = Ledger()
    fixed_ledger.record_transaction("wallet", "merchant_a", Decimal("100.00"))
    fixed_ledger.record_transaction("wallet", "merchant_b", Decimal("50.00"))

    global_total = sum(e.amount for e in fixed_ledger._entries)
    print(f"Double-entry global total: {global_total}")
    print(f"verify_invariant():        {fixed_ledger.verify_invariant()}")
    print(f"wallet balance:            {fixed_ledger.balance('wallet')}")
    print(f"merchant_a balance:        {fixed_ledger.balance('merchant_a')}")
    print(f"merchant_b balance:        {fixed_ledger.balance('merchant_b')}")
    return fixed_ledger, global_total


@app.cell
def _(mo):
    mo.md("""
    ## Edge Cases

    ### Decimal precision
    Floating point would give `0.01 + 0.02 = 0.030000000000000004`.
    Python's `Decimal` type uses arbitrary-precision base-10 arithmetic — no drift.

    ### Self-transfer
    Transferring money to the same account produces a net balance of zero.
    The invariant still holds. Useful for reconciliation no-ops.

    ### Invalid amounts
    Zero and negative amounts are rejected immediately — they would corrupt the ledger
    by creating an asymmetric entry pair.
    """)
    return


@app.cell
def _(Decimal, Ledger):
    # Decimal precision: no floating point drift
    precision_ledger = Ledger()
    precision_ledger.record_transaction("a", "b", Decimal("0.01"))
    precision_ledger.record_transaction("a", "b", Decimal("0.02"))
    print(f"0.01 + 0.02 with Decimal: {precision_ledger.balance('a')}")
    print(f"(float would be:          {0.01 + 0.02})")

    # Self-transfer
    self_ledger = Ledger()
    self_ledger.record_transaction("wallet", "wallet", Decimal("100.00"))
    print(f"\nSelf-transfer wallet balance: {self_ledger.balance('wallet')}")
    print(f"Invariant holds: {self_ledger.verify_invariant()}")
    return precision_ledger, self_ledger


@app.cell
def _(Decimal, Ledger):
    from ledger import InvariantViolationError

    error_ledger = Ledger()
    for bad_amount in [Decimal("0"), Decimal("-10.00")]:
        try:
            error_ledger.record_transaction("a", "b", bad_amount)
            print(f"BUG: {bad_amount} should have been rejected")
        except InvariantViolationError as exc:
            print(f"Rejected {bad_amount:>7}: {exc}")
    return InvariantViolationError, bad_amount, error_ledger


@app.cell
def _(mo):
    mo.md("""
    ## Reflection

    - Why does `verify_invariant()` always return `True` after valid transactions?
    - What happens if you insert a raw entry without a matching pair?
      (This is why production systems enforce the invariant at the database layer.)
    - How would you extend this to support multi-leg transactions
      (e.g., one payment splits fees across three accounts)?
    - Could you explain double-entry bookkeeping in a 2-minute interview answer?

    **Confidence score:** Rate yourself 1–5 on double-entry bookkeeping and log in PROGRESS.md.
    """)
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
