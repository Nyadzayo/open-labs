# labs/10-event-driven-payments/ — Event-Driven Payments + CQRS

**Purpose:** Event sourcing with CQRS — immutable event log, replay to rebuild state, separate read model.

## Depends on
- Nothing (standalone lab)

## Key files
- event_store.py: EventStore with append, get_events, all_events
- read_model.py: PaymentReadModel projection with apply, rebuild
- models.py: Event dataclass
- test_event_store.py: 12 tests covering store + read model

## Test
`pytest labs/10-event-driven-payments/ -v`
