import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    # Lab 05: Reconciliation Engine

    ## Why does reconciliation exist?

    Your internal ledger says transaction tx_123 was $100.00 with status SETTLED.
    The payment provider's settlement file says tx_123 was $99.50 with status CAPTURED.

    That $0.50 discrepancy doesn't announce itself. It silently accumulates across
    thousands of transactions. At month-end close, the books don't balance.
    Finance investigates manually. Revenue recognition is delayed. Auditors flag it.

    **Without reconciliation:** Money falls between systems. You discover it too late.

    **With reconciliation:** Every discrepancy is caught at ingestion time, categorized,
    and queued for investigation before it becomes a compliance problem.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## First Principles

    Reconciliation is a **join on transaction ID** between two independent sources of truth.

    The core mechanism:
    1. Internal ledger records every transaction as your system sees it
    2. Provider settlement file records every transaction as they processed it
    3. Reconciliation joins on `transaction_id` and flags any disagreement

    Four things can go wrong:
    - **MISSING_INTERNAL** — Provider has it, you don't (payment processed but not recorded)
    - **MISSING_PROVIDER** — You have it, provider doesn't (recorded but not settled)
    - **AMOUNT_MISMATCH** — Same transaction, different amounts (partial settlement, fee deduction)
    - **STATUS_MISMATCH** — Same transaction, different status (your SETTLED vs their CAPTURED)
    """)
    return


@app.cell
def _():
    # The smallest reconciliation system — two dicts, find the gaps
    from decimal import Decimal

    internal = {
        "tx_1": {"amount": Decimal("100.00"), "status": "SETTLED"},
        "tx_2": {"amount": Decimal("250.00"), "status": "SETTLED"},
    }
    provider = {
        "tx_1": {"amount": Decimal("100.00"), "status": "SETTLED"},
        "tx_3": {"amount": Decimal("75.00"), "status": "SETTLED"},
    }

    all_ids = set(internal) | set(provider)
    mismatches = []

    for tx_id in sorted(all_ids):
        i = internal.get(tx_id)
        p = provider.get(tx_id)
        if i is None:
            mismatches.append(f"{tx_id}: MISSING_INTERNAL (provider has it, we don't)")
        elif p is None:
            mismatches.append(f"{tx_id}: MISSING_PROVIDER (we have it, provider doesn't)")

    for m in mismatches:
        print(m)
    return


@app.cell
def _(mo):
    mo.md("""
    ## What breaks without reconciliation?

    Silent drift. No error is raised. No alert fires. The two systems just quietly
    disagree, and the divergence compounds over time.
    """)
    return


@app.cell
def _():
    # Simulate silent drift — no reconciliation, no detection
    from decimal import Decimal

    internal_ledger = [
        {"tx_id": "tx_1", "amount": Decimal("100.00")},
        {"tx_id": "tx_2", "amount": Decimal("200.00")},
        {"tx_id": "tx_3", "amount": Decimal("150.00")},
    ]

    # Provider secretly applied a 0.5% processing fee we didn't account for
    provider_settlements = [
        {"tx_id": "tx_1", "amount": Decimal("99.50")},   # -0.50
        {"tx_id": "tx_2", "amount": Decimal("199.00")},  # -1.00
        {"tx_id": "tx_3", "amount": Decimal("149.25")},  # -0.75
    ]

    internal_total = sum(r["amount"] for r in internal_ledger)
    provider_total = sum(r["amount"] for r in provider_settlements)

    print(f"Internal ledger total:    ${internal_total}")
    print(f"Provider settlement total: ${provider_total}")
    print(f"Silent discrepancy:        ${internal_total - provider_total}")
    print()
    print("Without reconciliation: books close with $2.25 unexplained variance.")
    print("With reconciliation: 3 AMOUNT_MISMATCH records flagged at ingestion time.")
    return


@app.cell
def _(mo):
    mo.md("""
    ## The 4 Mismatch Types

    ### MISSING_INTERNAL
    Provider settled a transaction we have no record of. Could mean:
    - Our system crashed after charging but before recording
    - A race condition between charge and ledger write
    - A refund processed on the provider side without our knowledge

    ### MISSING_PROVIDER
    We recorded a transaction the provider never settled. Could mean:
    - Payment was rejected after we recorded it as pending
    - Settlement file is incomplete (common with batch processing)
    - Transaction is in a limbo state awaiting manual review

    ### AMOUNT_MISMATCH
    Both sides have the transaction, but the amounts differ. Could mean:
    - Provider applied interchange fees
    - Partial authorization (customer's card only had partial funds)
    - Currency conversion rounding
    - Chargeback applied mid-settlement

    ### STATUS_MISMATCH
    Both sides have the transaction, but the status differs. Could mean:
    - CAPTURED on provider side (authorized, not yet settled)
    - SETTLED on our side (we moved it to settled prematurely)
    - REFUNDED on provider side (customer called bank directly)
    - DISPUTED — chargeback initiated
    """)
    return


@app.cell
def _():
    # All 4 mismatch types in one example
    from decimal import Decimal

    from reconciler import Record, reconcile

    internal = [
        Record("tx_1", Decimal("100.00"), "SETTLED"),   # amount will differ
        Record("tx_2", Decimal("200.00"), "SETTLED"),   # status will differ
        Record("tx_3", Decimal("150.00"), "SETTLED"),   # missing from provider
        # tx_4 missing from internal
    ]

    provider = [
        Record("tx_1", Decimal("99.50"),  "SETTLED"),   # amount mismatch
        Record("tx_2", Decimal("200.00"), "CAPTURED"),  # status mismatch
        # tx_3 missing from provider
        Record("tx_4", Decimal("75.00"),  "SETTLED"),   # missing from internal
    ]

    results = reconcile(internal, provider)
    for r in results:
        print(f"{r.transaction_id:6} | {r.mismatch_type:20} | internal={r.internal_value!r:10} provider={r.provider_value!r}")
    return


@app.cell
def _(mo):
    mo.md("""
    ## Edge Cases

    ### 1. Both sides empty
    Clean baseline — no mismatches. Reconciliation passes trivially.

    ### 2. Both amount AND status wrong on the same transaction
    One transaction can produce two mismatches. The engine reports both.
    Amount drift and status drift are independent problems requiring different remediation.

    ### 3. Large batch with mixed results
    Sort by transaction ID for deterministic output. Sorting ensures regression tests
    produce stable orderings regardless of dict iteration order.

    ### 4. Decimal precision
    Always use `Decimal`, never `float`. `float("99.99") != float("100.00") - float("0.01")`
    is a real bug in payment systems. Decimal arithmetic is exact.
    """)
    return


@app.cell
def _():
    from decimal import Decimal

    from reconciler import Record, reconcile

    # Edge case: both amount and status wrong
    internal = [Record("tx_1", Decimal("100.00"), "CAPTURED")]
    provider = [Record("tx_1", Decimal("99.00"),  "SETTLED")]

    results = reconcile(internal, provider)
    print(f"Mismatches for tx_1: {len(results)}")
    for r in results:
        print(f"  {r.mismatch_type}: internal={r.internal_value!r} provider={r.provider_value!r}")

    # Edge case: float vs Decimal precision trap
    print()
    float_result = 100.00 - 0.01 == 99.99
    decimal_result = Decimal("100.00") - Decimal("0.01") == Decimal("99.99")
    print(f"float: 100.00 - 0.01 == 99.99 → {float_result}")
    print(f"Decimal: 100.00 - 0.01 == 99.99 → {decimal_result}")
    return


@app.cell
def _(mo):
    mo.md("""
    ## Reflection

    - Could you explain to a finance team why their month-end close failed without using technical jargon?
    - What's the difference between reconciliation and idempotency? (Hint: timing)
    - How would you handle a MISSING_PROVIDER that's just delayed — settlement files arrive T+2?
    - What SLA would you put on reconciliation runs? Hourly? Real-time?

    **Confidence score:** Rate yourself 1-5 on reconciliation and log it in PROGRESS.md
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
