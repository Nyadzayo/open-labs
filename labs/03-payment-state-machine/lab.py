import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    # Lab 03: Payment State Machine

    ## Why does this exist?

    A payment goes through a lifecycle: it starts as PENDING, gets AUTHORIZED by
    the card network, gets CAPTURED (money moves), and finally SETTLED.

    Without a state machine, nothing stops your code from transitioning a PENDING
    payment directly to REFUNDED — which makes no sense and corrupts your ledger.

    A state machine **explicitly defines which transitions are allowed** and rejects
    everything else.

    ## The States

    ```
    PENDING ─── AUTHORIZED ─── CAPTURED ─── SETTLED
       │            │    ╲          │
       ▼            ▼     ▼        ▼
    CANCELLED    FAILED  CANCELLED REFUNDED
    ```
    """)
    return


@app.cell
def _():
    from state_machine import InvalidTransitionError, PaymentState, transition

    # Happy path — this works
    state = PaymentState.PENDING
    state = transition(state, PaymentState.AUTHORIZED)
    state = transition(state, PaymentState.CAPTURED)
    state = transition(state, PaymentState.SETTLED)
    print(f"Happy path result: {state.value}")
    return InvalidTransitionError, PaymentState, state, transition


@app.cell
def _(InvalidTransitionError, PaymentState, transition):
    # What breaks without it — try to skip from PENDING to REFUNDED
    try:
        transition(PaymentState.PENDING, PaymentState.REFUNDED)
        print("BUG: This should not happen!")
    except InvalidTransitionError as e:
        print(f"Caught: {e}")
        print("The state machine prevented an invalid transition.")
    return


@app.cell
def _(mo):
    mo.md("""
    ## Reflection

    - What happens if you don't enforce state transitions at the database level?
    - How would you add a new state (e.g., PARTIALLY_REFUNDED)?
    - Could you explain this lifecycle in a 2-minute interview answer?

    **Confidence score:** Rate yourself 1-5 and log in PROGRESS.md
    """)
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
