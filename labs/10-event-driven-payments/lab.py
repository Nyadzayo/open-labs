import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    # Lab 10: Event-Driven Payment Notifications + CQRS

    ## Why event sourcing?

    A payment is captured. The status column flips from CAPTURED to SETTLED.
    Three months later, an auditor asks: "When exactly was this payment authorised?
    Who changed the status? Was there a refund attempt before the settlement?"

    You cannot answer. The mutable record kept only the latest state. History is gone.

    **Event sourcing** solves this by treating state as a derived value.
    Instead of updating a row, you append an immutable event:

    ```
    PaymentCreated    → {amount: "100.00", currency: "USD"}
    PaymentAuthorized → {auth_code: "ABC123"}
    PaymentCaptured   → {captured_at: "2024-01-15T10:30:00Z"}
    PaymentSettled    → {settled_at: "2024-01-17T08:00:00Z"}
    ```

    The current state is always derivable by replaying the event log.
    You never lose history because you never overwrite it.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## The mutable-state problem — what you lose

    Consider a traditional mutable design:

    ```python
    # Mutable: update in place
    payment = db.get("pay_001")
    payment.status = "SETTLED"
    payment.updated_at = now()
    db.save(payment)
    ```

    What's lost:
    - When was it authorised? (overwritten)
    - Was there a failed capture attempt? (never recorded)
    - What was the original amount before a partial refund? (overwritten)
    - Who processed the settlement? (no record)

    You can add `updated_at` and `updated_by` columns, but that only captures
    the last change. For a full trail you'd add an audit log table — which is
    exactly event sourcing, done manually and incompletely.

    Event sourcing makes the audit log the primary store.
    The read model is derived from it, not the other way around.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## First principles: events as immutable facts

    Three rules:
    1. **Events are facts** — they describe something that happened, past tense.
       `PaymentCreated`, not `CreatePayment`. Once appended, they never change.
    2. **The store is append-only** — no updates, no deletes. Ever.
    3. **State is a fold** — current state = `reduce(apply, events, initial_state)`.

    ```python
    events = [
        Event("PaymentCreated",    data={"amount": "100.00"}),
        Event("PaymentAuthorized", data={}),
        Event("PaymentCaptured",   data={}),
    ]

    # State is rebuilt by replaying:
    state = {}
    for event in events:
        state = apply(state, event)

    # state == {"amount": "100.00", "status": "CAPTURED"}
    ```

    This means you can always reconstruct any past state by replaying
    events up to a given point in time.
    """)
    return


@app.cell
def _():
    # Minimal event store — no framework needed
    import sys
    sys.path.insert(0, ".")

    from event_store import EventStore

    store = EventStore()

    # Append events for a payment
    e1 = store.append("pay_001", "PaymentCreated", {"amount": "100.00", "currency": "USD"})
    e2 = store.append("pay_001", "PaymentAuthorized", {"auth_code": "ABC123"})
    e3 = store.append("pay_001", "PaymentCaptured", {})

    # A second independent payment
    e4 = store.append("pay_002", "PaymentCreated", {"amount": "75.00", "currency": "EUR"})

    print(f"Total events in store: {len(store.all_events())}")
    print()
    print("Events for pay_001:")
    for e in store.get_events("pay_001"):
        print(f"  v{e.version}  {e.event_type:<22}  {e.data}")
    print()
    print("Events for pay_002:")
    for e in store.get_events("pay_002"):
        print(f"  v{e.version}  {e.event_type:<22}  {e.data}")
    return (EventStore, e1, e2, e3, e4, store, sys)


@app.cell
def _(mo):
    mo.md("""
    ## CQRS: separating writes from reads

    **CQRS** — Command Query Responsibility Segregation — splits the system in two:

    - **Write side**: append events to the event store (the command)
    - **Read side**: a projection (read model) that consumes events and builds
      a query-optimised view of state

    ```
    Client
      │
      ├─── Command (write) ──→ EventStore.append(...)
      │                              │
      │                         event published
      │                              │
      │                              ↓
      │                        ReadModel.apply(event)
      │
      └─── Query (read) ────→ ReadModel.get(payment_id)
    ```

    The read model can be optimised for query patterns independently of the
    event structure. You can have multiple read models from the same events:
    one for payment status, another for settlement totals, another for fraud signals.

    Crucially: the read model is **disposable**. If it gets corrupted or you
    need a new structure, rebuild it by replaying all events from the store.
    """)
    return


@app.cell
def _(store):
    # CQRS read model — projection built from events
    from read_model import PaymentReadModel

    read_model = PaymentReadModel()

    # Build the read model from all events in the store
    read_model.rebuild(store.all_events())

    print("Read model state after rebuild:")
    for pid, state in read_model.list_all().items():
        print(f"  {pid}: status={state['status']}  version={state['version']}  data={state}")
    return (PaymentReadModel, read_model)


@app.cell
def _(mo):
    mo.md("""
    ## Full payment lifecycle

    A payment in a card network goes through predictable states:

    ```
    PaymentCreated
         ↓
    PaymentAuthorized   ← bank confirms funds exist
         ↓
    PaymentCaptured     ← merchant requests settlement
         ↓
    PaymentSettled      ← funds transferred
         ↓ (if needed)
    PaymentRefunded     ← funds returned to customer
    ```

    Each transition is an event. The read model applies each event
    to update the projected state.
    """)
    return


@app.cell
def _():
    # Full lifecycle demonstration
    import sys
    sys.path.insert(0, ".")

    from event_store import EventStore
    from read_model import PaymentReadModel

    lifecycle_store = EventStore()
    lifecycle_model = PaymentReadModel()

    lifecycle_events = [
        ("pay_full", "PaymentCreated",    {"amount": "250.00", "currency": "GBP"}),
        ("pay_full", "PaymentAuthorized", {"auth_code": "XYZ789"}),
        ("pay_full", "PaymentCaptured",   {}),
        ("pay_full", "PaymentSettled",    {"batch_id": "BATCH_20240117"}),
    ]

    refund_events = [
        ("pay_refund", "PaymentCreated",  {"amount": "50.00", "currency": "USD"}),
        ("pay_refund", "PaymentCaptured", {}),
        ("pay_refund", "PaymentRefunded", {"reason": "customer_request"}),
    ]

    print("Full lifecycle (Created → Settled):")
    for aggregate_id, event_type, data in lifecycle_events:
        event = lifecycle_store.append(aggregate_id, event_type, data)
        lifecycle_model.apply(event)
        state = lifecycle_model.get(aggregate_id)
        print(f"  v{event.version}  {event_type:<22} → status={state['status']}")

    print()
    print("Refund path (Created → Captured → Refunded):")
    for aggregate_id, event_type, data in refund_events:
        event = lifecycle_store.append(aggregate_id, event_type, data)
        lifecycle_model.apply(event)
        state = lifecycle_model.get(aggregate_id)
        print(f"  v{event.version}  {event_type:<22} → status={state['status']}")
    return (
        EventStore,
        PaymentReadModel,
        aggregate_id,
        data,
        event,
        event_type,
        lifecycle_events,
        lifecycle_model,
        lifecycle_store,
        refund_events,
        state,
        sys,
    )


@app.cell
def _(mo):
    mo.md("""
    ## Rebuilding state from scratch

    The read model is derived — it can always be discarded and rebuilt.
    This is the killer feature of event sourcing.

    Scenarios where you need to rebuild:
    - Bug corrupted the read model projection
    - You need a new query shape (add a new field to the projection)
    - You want to audit what state looked like at a specific point in time
    - You're onboarding a new service that needs historical state

    Rebuild is simple: clear the read model, replay all events in order.
    """)
    return


@app.cell
def _(lifecycle_model, lifecycle_store):
    # Demonstrate rebuild
    print("State BEFORE rebuild:")
    for pid, s in lifecycle_model.list_all().items():
        print(f"  {pid}: {s['status']}")

    # Corrupt the model to show rebuild fixes it
    lifecycle_model._payments["pay_full"]["status"] = "CORRUPTED"
    print()
    print("State AFTER corruption:")
    for pid, s in lifecycle_model.list_all().items():
        print(f"  {pid}: {s['status']}")

    # Rebuild from event store
    lifecycle_model.rebuild(lifecycle_store.all_events())
    print()
    print("State AFTER rebuild from event store:")
    for pid, s in lifecycle_model.list_all().items():
        print(f"  {pid}: {s['status']}")
    return (pid, s)


@app.cell
def _(mo):
    mo.md("""
    ## Break it: the mutable-state world (no audit trail)

    Here is what happens when you use mutable state instead of events.
    Simulate the same payment lifecycle with a simple dict — the "database row" approach.
    """)
    return


@app.cell
def _():
    # Mutable state — no events, no history
    mutable_payment: dict = {}

    def create_payment(pid: str, amount: str) -> None:
        mutable_payment[pid] = {"status": "PENDING", "amount": amount}

    def authorize_payment(pid: str) -> None:
        mutable_payment[pid]["status"] = "AUTHORIZED"
        # Previous status is gone — was it PENDING? FAILED? We'll never know.

    def capture_payment(pid: str) -> None:
        mutable_payment[pid]["status"] = "CAPTURED"

    def settle_payment(pid: str) -> None:
        mutable_payment[pid]["status"] = "SETTLED"

    create_payment("pay_mutable", "100.00")
    authorize_payment("pay_mutable")
    capture_payment("pay_mutable")
    settle_payment("pay_mutable")

    print("Current state (mutable):")
    print(f"  {mutable_payment}")
    print()
    print("Questions you can't answer:")
    print("  - When was it authorised?         UNKNOWN")
    print("  - What was the auth code?          UNKNOWN")
    print("  - Was there a failed capture?      UNKNOWN")
    print("  - Who settled it?                  UNKNOWN")
    print("  - What state was it in 2 hours ago? UNKNOWN")
    return (
        authorize_payment,
        capture_payment,
        create_payment,
        mutable_payment,
        settle_payment,
    )


@app.cell
def _(mo):
    mo.md("""
    ## Version ordering guarantees correctness

    Each event has a version number scoped to its aggregate.
    `pay_001` has its own version sequence; `pay_002` has its own.
    They are independent.

    This gives you:
    - **Ordering within an aggregate**: events applied in version order
    - **Optimistic concurrency**: detect conflicts (two writers both on v3)
    - **Point-in-time replay**: "what was the state after event v2?"
    """)
    return


@app.cell
def _():
    import sys
    sys.path.insert(0, ".")

    from event_store import EventStore

    version_store = EventStore()

    # Two independent aggregates — versions are independent
    version_store.append("pay_A", "PaymentCreated", {})
    version_store.append("pay_B", "PaymentCreated", {})
    version_store.append("pay_A", "PaymentAuthorized", {})
    version_store.append("pay_B", "PaymentAuthorized", {})
    version_store.append("pay_A", "PaymentCaptured", {})

    print("Versions for pay_A:")
    for e in version_store.get_events("pay_A"):
        print(f"  v{e.version}  {e.event_type}")

    print()
    print("Versions for pay_B:")
    for e in version_store.get_events("pay_B"):
        print(f"  v{e.version}  {e.event_type}")

    print()
    print("pay_A has 3 events, pay_B has 2 — each independent, starting at v1")
    return (EventStore, e, version_store, sys)


@app.cell
def _(mo):
    mo.md("""
    ## Reflection

    ### What this lab demonstrates

    1. **Immutable events as the source of truth** — state is derived, never stored
       directly. The event log is the database; the read model is a cache.

    2. **CQRS separation** — writes go to the event store (append-only); reads come
       from the projection (query-optimised). Each side can evolve independently.

    3. **Full audit trail by default** — every state transition is recorded with
       a timestamp and version. Auditors, regulators, and on-call engineers can
       always answer "what happened and when?"

    4. **Rebuild as a first-class operation** — the read model is disposable.
       Fix a bug in the projection, rebuild from events, get correct state.
       No data migration required.

    5. **Independent aggregate versioning** — each payment has its own version
       sequence. Optimistic concurrency control is a natural extension.

    ### What a production system adds

    - **Event bus / message broker**: Kafka, SNS/SQS — publish events to subscribers
    - **Snapshots**: cache aggregate state every N events to speed up replay
    - **Optimistic concurrency**: reject writes where expected version != actual version
    - **Event schema registry**: Avro/Protobuf schemas, versioned event contracts
    - **Multiple projections**: status view, settlement totals, fraud signals — all from the same events
    - **Persistent event store**: EventStoreDB, Postgres with append-only guarantees

    ### Interview answer

    > "We use event sourcing for payments because regulators require a complete
    > audit trail and mutable state can't provide it. Every state transition —
    > created, authorised, captured, settled, refunded — is an immutable event
    > appended to the store. The current status is a projection rebuilt by
    > replaying events. CQRS keeps the write path (event append) decoupled from
    > the read path (status queries), so each can be optimised independently.
    > If the read model gets corrupted or we need a new query shape, we replay
    > the event log and rebuild from scratch."

    ---

    **Confidence score:** 9/10

    The core event sourcing and CQRS mechanics are fully implemented and tested.
    The main production gap is persistence (this uses in-memory lists) and
    an event bus for notifying downstream consumers. Those are infrastructure
    concerns — the domain logic here maps 1:1 to production EventStoreDB or
    Postgres-backed implementations.
    """)
    return


@app.cell
def _(mo):
    return (mo,)


if __name__ == "__main__":
    app.run()
