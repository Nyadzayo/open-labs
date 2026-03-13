# Lab 10: Event-Driven Payment Notifications + CQRS

## Role Relevance
Backend Engineer — event-driven architecture is core to modern fintech systems.

## Business Problem
Mutable database: payment status updated in place. Auditor asks "when was this payment authorized?" — you can't answer. Event sourcing: every state change is an immutable event. Full audit trail forever.

## First Principles
- **Event**: Immutable fact that happened (PaymentCreated, PaymentCaptured)
- **Event Store**: Append-only log of all events
- **Replay**: Rebuild current state by replaying events from the beginning
- **CQRS**: Write to event store, read from a projection (read model)

## How to Test
```bash
pytest labs/10-event-driven-payments/ -v
```

## Edge Cases Covered
- Event version auto-increments per aggregate
- Independent aggregates have independent versions
- Full lifecycle: Created → Authorized → Captured → Settled
- Refund path: Created → Captured → Refunded
- Rebuild from scratch matches incremental apply
- Duplicate event application is safe

## What This Proves
"Implemented event-driven payment system with event sourcing and CQRS read model separation."
