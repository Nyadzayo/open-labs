"""Tests for event store and CQRS read model."""

from __future__ import annotations

import pytest
from event_store import EventStore
from read_model import PaymentReadModel


@pytest.fixture
def store() -> EventStore:
    return EventStore()


@pytest.fixture
def read_model() -> PaymentReadModel:
    return PaymentReadModel()


def test_append_event(store: EventStore) -> None:
    event = store.append("pay_001", "PaymentCreated", {"amount": "100.00"})
    assert event.aggregate_id == "pay_001"
    assert event.event_type == "PaymentCreated"
    assert event.version == 1


def test_version_increments(store: EventStore) -> None:
    e1 = store.append("pay_001", "PaymentCreated", {})
    e2 = store.append("pay_001", "PaymentAuthorized", {})
    assert e1.version == 1
    assert e2.version == 2


def test_get_events_by_aggregate(store: EventStore) -> None:
    store.append("pay_001", "PaymentCreated", {})
    store.append("pay_002", "PaymentCreated", {})
    store.append("pay_001", "PaymentAuthorized", {})
    events = store.get_events("pay_001")
    assert len(events) == 2
    assert all(e.aggregate_id == "pay_001" for e in events)


def test_all_events(store: EventStore) -> None:
    store.append("pay_001", "PaymentCreated", {})
    store.append("pay_002", "PaymentCreated", {})
    assert len(store.all_events()) == 2


def test_independent_aggregate_versions(store: EventStore) -> None:
    store.append("pay_001", "PaymentCreated", {})
    store.append("pay_002", "PaymentCreated", {})
    events_1 = store.get_events("pay_001")
    events_2 = store.get_events("pay_002")
    assert events_1[0].version == 1
    assert events_2[0].version == 1


# Read model tests

def test_read_model_created(
    store: EventStore, read_model: PaymentReadModel
) -> None:
    event = store.append(
        "pay_001", "PaymentCreated", {"amount": "100.00", "currency": "USD"}
    )
    read_model.apply(event)
    payment = read_model.get("pay_001")
    assert payment is not None
    assert payment["status"] == "PENDING"
    assert payment["amount"] == "100.00"


def test_read_model_lifecycle(
    store: EventStore, read_model: PaymentReadModel
) -> None:
    events = [
        store.append("pay_001", "PaymentCreated", {"amount": "100.00"}),
        store.append("pay_001", "PaymentAuthorized", {}),
        store.append("pay_001", "PaymentCaptured", {}),
        store.append("pay_001", "PaymentSettled", {}),
    ]
    for event in events:
        read_model.apply(event)
    payment = read_model.get("pay_001")
    assert payment is not None
    assert payment["status"] == "SETTLED"
    assert payment["version"] == 4


def test_read_model_rebuild(
    store: EventStore, read_model: PaymentReadModel
) -> None:
    store.append("pay_001", "PaymentCreated", {"amount": "50.00"})
    store.append("pay_001", "PaymentAuthorized", {})
    store.append("pay_002", "PaymentCreated", {"amount": "75.00"})

    read_model.rebuild(store.all_events())
    assert read_model.get("pay_001")["status"] == "AUTHORIZED"
    assert read_model.get("pay_002")["status"] == "PENDING"


def test_read_model_refund(
    store: EventStore, read_model: PaymentReadModel
) -> None:
    events = [
        store.append("pay_001", "PaymentCreated", {"amount": "100.00"}),
        store.append("pay_001", "PaymentCaptured", {}),
        store.append("pay_001", "PaymentRefunded", {}),
    ]
    for event in events:
        read_model.apply(event)
    assert read_model.get("pay_001")["status"] == "REFUNDED"


def test_read_model_list_all(
    store: EventStore, read_model: PaymentReadModel
) -> None:
    read_model.apply(store.append("pay_001", "PaymentCreated", {"amount": "50.00"}))
    read_model.apply(store.append("pay_002", "PaymentCreated", {"amount": "75.00"}))
    all_payments = read_model.list_all()
    assert len(all_payments) == 2


def test_duplicate_event_safe(
    store: EventStore, read_model: PaymentReadModel
) -> None:
    """Applying same event type twice doesn't break state."""
    event = store.append("pay_001", "PaymentCreated", {"amount": "100.00"})
    read_model.apply(event)
    read_model.apply(event)  # Duplicate — overwrites with same data
    assert read_model.get("pay_001")["status"] == "PENDING"
