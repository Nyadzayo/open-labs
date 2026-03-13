import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    # Lab 09: Async Settlement Processing

    ## Why async settlement?

    A customer taps their card. The payment is **authorised** in under 200ms — the
    bank confirms the funds exist and reserves them. But the money does not move yet.

    **Settlement** — the actual transfer of funds between banks — happens on a batch
    schedule. Banks use networks like ACH (1-2 days) or Fedwire (same day). Card
    networks run settlement windows. None of this is real-time.

    This creates a fundamental mismatch:
    - Capture: milliseconds
    - Settlement: hours to days

    You cannot block a web request for 2 days. Settlement **must** happen
    asynchronously, in a background worker, with retry logic and a way to handle
    failures without losing track of money.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Sync vs Async: Why you can't settle inline

    Imagine a naive synchronous approach:

    ```python
    def capture_payment(payment_id: str) -> None:
        payment = db.get(payment_id)
        payment.status = CAPTURED

        # WRONG: calling settlement provider inline
        result = bank_provider.settle(payment)   # blocks for up to 30s
        payment.status = SETTLED
        db.save(payment)
    ```

    Problems at scale:
    1. **Timeouts** — bank APIs time out under load. Your web worker dies mid-request.
       The payment is captured but not settled. You have no record of where it failed.
    2. **Thread exhaustion** — 50 concurrent settlements × 10s each = 500 thread-seconds.
       Your server runs out of workers. All new requests queue up.
    3. **No retry** — if the provider returns 503, you have to tell the customer it failed,
       even though a retry 30 seconds later would have succeeded.
    4. **No audit trail** — sync failures leave no trace. Async tasks leave records.

    The correct model: capture returns immediately, settlement task is enqueued.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Task Queue Concepts

    A task queue is a list of work items that workers consume independently of the
    request/response cycle.

    ```
    Web Request                    Worker Process
    ─────────────                  ──────────────
    POST /capture                  loop:
      → save payment               │  task = queue.pop()
      → enqueue(settle, pay_id)    │  settle(task.payment_id)
      → return 200 immediately     │  handle result
                                   └──────────────
    ```

    Three components:
    - **Queue**: ordered list of tasks waiting to be processed
    - **Worker**: process that consumes tasks one at a time (or in parallel)
    - **Dead-letter queue (DLQ)**: where tasks go when they fail beyond recovery

    In production: Celery + Redis, AWS SQS, RabbitMQ, Google Pub/Sub.
    Here: a plain Python list that behaves identically.
    """)
    return


@app.cell
def _():
    # Minimal working task queue — no framework needed to understand the concept
    from collections import deque

    class SimpleQueue:
        def __init__(self) -> None:
            self._items: deque[str] = deque()

        def enqueue(self, item: str) -> None:
            self._items.append(item)

        def dequeue(self) -> str | None:
            return self._items.popleft() if self._items else None

        def __len__(self) -> int:
            return len(self._items)

    q: SimpleQueue = SimpleQueue()
    q.enqueue("settle:pay_001")
    q.enqueue("settle:pay_002")
    q.enqueue("settle:pay_003")

    print(f"Queue depth: {len(q)}")
    while (task := q.dequeue()) is not None:
        print(f"  Processing: {task}")
    print(f"Queue depth after drain: {len(q)}")
    return (SimpleQueue,)


@app.cell
def _(mo):
    mo.md("""
    ## Idempotency in Tasks

    What happens if a worker crashes after settling but before marking the task done?
    The task gets re-delivered and processed again.

    Without idempotency: double settlement. Customer charged twice. Catastrophic.

    With idempotency: second call is a no-op.

    ```python
    def process_next(self) -> str:
        ...
        # Idempotency check — already settled means nothing to do
        if payment.status == PaymentStatus.SETTLED:
            return "already_settled"
        ...
    ```

    The status check is the guard. If the first run completed and set status=SETTLED,
    the second run sees SETTLED and exits immediately. The payment is not touched again.

    This is why status transitions must be **atomic** in production — use database
    transactions with `SELECT FOR UPDATE` to prevent two workers from processing the
    same payment simultaneously.
    """)
    return


@app.cell
def _():
    # Demonstrate idempotency with the actual SettlementProcessor
    import sys
    sys.path.insert(0, ".")

    from models import PaymentStatus
    from settlement import Payment, SettlementProcessor

    processor = SettlementProcessor()
    payment = Payment(id="pay_demo", amount="250.00")
    processor.payments["pay_demo"] = payment

    # Enqueue twice (simulate duplicate delivery)
    processor.enqueue("pay_demo")
    processor.enqueue("pay_demo")

    result1 = processor.process_next()
    result2 = processor.process_next()

    print(f"First processing:  {result1}")
    print(f"Second processing: {result2}")
    print(f"Final status:      {payment.status}")
    print(f"Settled list:      {processor.settled}")
    return (Payment, PaymentStatus, SettlementProcessor, payment, processor, result1, result2)


@app.cell
def _(mo):
    mo.md("""
    ## Retry Strategies

    Not all failures are equal. The classification determines what happens next:

    | Failure type      | Example                        | Action                  |
    |-------------------|--------------------------------|-------------------------|
    | Transient         | 503, network timeout, DB lock  | Retry with backoff      |
    | Permanent         | Invalid account, fraud block   | Move to DLQ immediately |
    | Max retries hit   | 3 transient failures in a row  | Move to DLQ             |

    **Transient failures** are temporary. The provider was overloaded or briefly
    unreachable. Retrying after a short wait usually succeeds.

    **Permanent failures** will never succeed no matter how many times you retry.
    A payment to a closed account will always be rejected. Retrying wastes resources
    and delays the failure signal. Move to DLQ immediately.

    **Backoff** between retries is critical. Retrying immediately under load makes
    things worse. In production: exponential backoff with jitter.
    Here we keep it simple — re-enqueue to the back of the queue.
    """)
    return


@app.cell
def _(Payment, SettlementProcessor):
    from models import SettlementResult

    # Show retry behaviour with a function that fails twice then succeeds
    proc_retry = SettlementProcessor()
    proc_retry.payments["pay_retry"] = Payment(id="pay_retry", amount="75.00")

    attempt_log: list[str] = []
    call_count = 0

    def flaky_provider(p: Payment) -> SettlementResult:
        global call_count
        call_count += 1
        if call_count < 3:
            attempt_log.append(f"attempt {call_count}: TRANSIENT_FAILURE")
            return SettlementResult.TRANSIENT_FAILURE
        attempt_log.append(f"attempt {call_count}: SUCCESS")
        return SettlementResult.SUCCESS

    proc_retry.set_settle_fn(flaky_provider)
    proc_retry.enqueue("pay_retry")

    while proc_retry.queue:
        result = proc_retry.process_next()
        print(f"  process_next() → {result}")

    print()
    for log_entry in attempt_log:
        print(f"  {log_entry}")
    print(f"\nFinal status: {proc_retry.payments['pay_retry'].status}")
    return (SettlementResult, attempt_log, call_count, flaky_provider, proc_retry)


@app.cell
def _(mo):
    mo.md("""
    ## Dead-Letter Queues

    A dead-letter queue (DLQ) is the destination for tasks that cannot be processed.
    They land in the DLQ instead of being discarded so that:

    1. **Humans can review them** — a payment that keeps failing needs investigation
    2. **Audit trail is preserved** — you know exactly which payments failed and why
    3. **Re-drive is possible** — once the root cause is fixed, you can replay DLQ items

    Three paths to the DLQ in this lab:
    - Invalid state (payment not CAPTURED): can't settle what isn't captured
    - Max retries exceeded: transient failures that didn't clear
    - Permanent failure: provider explicitly rejected the payment

    In production (AWS SQS, Celery):
    - Configure `maxReceiveCount` on the source queue
    - DLQ receives the message automatically after N failures
    - Alarm on DLQ depth > 0 — any DLQ item needs human attention
    """)
    return


@app.cell
def _(Payment, PaymentStatus, SettlementProcessor):
    from models import SettlementResult as SR

    proc_dlq = SettlementProcessor()

    # Payment 1: permanent failure → DLQ immediately
    proc_dlq.payments["pay_perm"] = Payment(id="pay_perm", amount="500.00")
    proc_dlq.set_settle_fn(lambda _: SR.PERMANENT_FAILURE)
    proc_dlq.enqueue("pay_perm")
    r1 = proc_dlq.process_next()

    # Payment 2: wrong state → DLQ immediately
    p2 = Payment(id="pay_wrong", amount="200.00")
    p2.status = PaymentStatus.PENDING
    proc_dlq.payments["pay_wrong"] = p2
    proc_dlq.enqueue("pay_wrong")
    r2 = proc_dlq.process_next()

    # Payment 3: max retries → DLQ after 3 attempts
    proc_dlq.payments["pay_exhaust"] = Payment(id="pay_exhaust", amount="150.00")
    proc_dlq.set_settle_fn(lambda _: SR.TRANSIENT_FAILURE)
    proc_dlq.enqueue("pay_exhaust")
    r3_results: list[str] = []
    while proc_dlq.queue:
        r3_results.append(proc_dlq.process_next())

    print(f"Permanent failure result:  {r1}")
    print(f"Wrong state result:        {r2}")
    print(f"Max retries results:       {r3_results}")
    print(f"\nDLQ depth: {len(proc_dlq.dlq)}")
    for task in proc_dlq.dlq:
        print(f"  DLQ entry: payment_id={task.payment_id}, attempts={task.attempts}")
    return (SR, p2, proc_dlq, r1, r2, r3_results)


@app.cell
def _(mo):
    mo.md("""
    ## Live Demo: Full Settlement Pipeline

    Simulate a batch of 5 payments with mixed outcomes:
    - pay_000: succeeds first try
    - pay_001: transient failure, succeeds on retry
    - pay_002: permanent failure → DLQ
    - pay_003: max retries exhausted → DLQ
    - pay_004: succeeds first try
    """)
    return


@app.cell
def _(Payment, SettlementProcessor):
    from models import SettlementResult as SR2

    demo = SettlementProcessor()

    # Create payments
    for i in range(5):
        demo.payments[f"pay_{i:03d}"] = Payment(id=f"pay_{i:03d}", amount=f"{(i + 1) * 50}.00")
        demo.enqueue(f"pay_{i:03d}")

    # Track per-payment behaviour
    call_counts: dict[str, int] = {}

    def demo_settle(p: Payment) -> SR2:
        call_counts[p.id] = call_counts.get(p.id, 0) + 1
        n = call_counts[p.id]
        if p.id == "pay_001" and n < 2:
            return SR2.TRANSIENT_FAILURE
        if p.id == "pay_002":
            return SR2.PERMANENT_FAILURE
        if p.id == "pay_003":
            return SR2.TRANSIENT_FAILURE  # always fails → exhausts retries
        return SR2.SUCCESS

    demo.set_settle_fn(demo_settle)

    print("Processing queue...")
    step = 0
    while demo.queue:
        step += 1
        result = demo.process_next()
        print(f"  step {step:02d}: {result}  (queue={len(demo.queue)}, dlq={len(demo.dlq)})")

    print("\nSummary:")
    print(f"  Settled:  {demo.settled}")
    print(f"  DLQ:      {[t.payment_id for t in demo.dlq]}")
    print("  Statuses:")
    for pid, pmt in demo.payments.items():
        print(f"    {pid}: {pmt.status}")
    return (SR2, call_counts, demo, demo_settle, step)


@app.cell
def _(mo):
    mo.md("""
    ## Reflection

    ### What this lab demonstrates

    1. **Async decoupling** — settlement runs independently of the HTTP request cycle.
       Capture is fast; settlement is reliable.

    2. **Idempotent tasks** — the SETTLED status check makes re-delivery safe.
       Duplicate tasks are no-ops, not double settlements.

    3. **Failure classification** — transient vs permanent is a first-class distinction.
       The retry strategy is determined by failure type, not by a blanket "retry everything".

    4. **Dead-letter queue** — failed tasks are never silently dropped. They land in
       the DLQ where a human (or automated re-drive job) can investigate.

    5. **State machine integrity** — only CAPTURED payments can be settled.
       A payment in PENDING or AUTHORIZED state going to the DLQ protects against
       settling money that was never confirmed.

    ### What a production system adds

    - **Celery + Redis/SQS**: distributed workers, horizontal scaling
    - **Exponential backoff**: `delay = base * 2^attempt` with jitter
    - **Visibility timeout**: task locked to one worker to prevent duplicate processing
    - **DLQ alarms**: CloudWatch / PagerDuty alert when DLQ depth > 0
    - **Re-drive API**: replay DLQ items after fixing the root cause
    - **Idempotency at DB level**: `SELECT FOR UPDATE` prevents race conditions

    ### Interview answer

    > "Settlement is inherently async — bank networks operate on batch windows, not
    > real-time. We enqueue a settlement task on capture and process it in a Celery
    > worker. The task is idempotent: if re-delivered, the SETTLED status check exits
    > early. Transient failures retry up to 3 times; permanent failures skip retries.
    > Exhausted tasks land in a dead-letter queue where ops can investigate and re-drive.
    > We alarm on DLQ depth > 0 because any item there represents money that needs
    > human attention."

    ---

    **Confidence score:** 9/10

    The processor covers all production failure modes in under 100 lines. The main
    thing missing is backoff delay simulation — in real Celery you'd use
    `self.retry(countdown=2**self.request.retries)`. The concepts map 1:1.
    """)
    return


@app.cell
def _(mo):
    return (mo,)


if __name__ == "__main__":
    app.run()
