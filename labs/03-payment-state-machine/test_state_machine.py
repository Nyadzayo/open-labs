"""Tests for payment state machine transitions."""

from __future__ import annotations

import pytest
from state_machine import InvalidTransitionError, PaymentState, transition

# === Valid transitions ===


@pytest.mark.parametrize(
    "from_state,to_state",
    [
        (PaymentState.PENDING, PaymentState.AUTHORIZED),
        (PaymentState.PENDING, PaymentState.CANCELLED),
        (PaymentState.AUTHORIZED, PaymentState.CAPTURED),
        (PaymentState.AUTHORIZED, PaymentState.CANCELLED),
        (PaymentState.AUTHORIZED, PaymentState.FAILED),
        (PaymentState.CAPTURED, PaymentState.SETTLED),
        (PaymentState.CAPTURED, PaymentState.REFUNDED),
    ],
)
def test_valid_transition(
    from_state: PaymentState, to_state: PaymentState
) -> None:
    result = transition(from_state, to_state)
    assert result == to_state


# === Invalid transitions ===


@pytest.mark.parametrize(
    "from_state,to_state",
    [
        # Can't skip states
        (PaymentState.PENDING, PaymentState.CAPTURED),
        (PaymentState.PENDING, PaymentState.SETTLED),
        (PaymentState.PENDING, PaymentState.REFUNDED),
        (PaymentState.AUTHORIZED, PaymentState.SETTLED),
        (PaymentState.AUTHORIZED, PaymentState.REFUNDED),
        # Terminal states can't transition
        (PaymentState.SETTLED, PaymentState.REFUNDED),
        (PaymentState.SETTLED, PaymentState.PENDING),
        (PaymentState.REFUNDED, PaymentState.SETTLED),
        (PaymentState.CANCELLED, PaymentState.PENDING),
        (PaymentState.FAILED, PaymentState.AUTHORIZED),
        # Can't go backwards
        (PaymentState.CAPTURED, PaymentState.AUTHORIZED),
        (PaymentState.AUTHORIZED, PaymentState.PENDING),
    ],
)
def test_invalid_transition(
    from_state: PaymentState, to_state: PaymentState
) -> None:
    with pytest.raises(InvalidTransitionError) as exc_info:
        transition(from_state, to_state)
    assert exc_info.value.from_state == from_state
    assert exc_info.value.to_state == to_state


def test_full_happy_path() -> None:
    """Walk through the complete payment lifecycle."""
    state = PaymentState.PENDING
    state = transition(state, PaymentState.AUTHORIZED)
    state = transition(state, PaymentState.CAPTURED)
    state = transition(state, PaymentState.SETTLED)
    assert state == PaymentState.SETTLED


def test_refund_path() -> None:
    """Walk through payment -> refund."""
    state = PaymentState.PENDING
    state = transition(state, PaymentState.AUTHORIZED)
    state = transition(state, PaymentState.CAPTURED)
    state = transition(state, PaymentState.REFUNDED)
    assert state == PaymentState.REFUNDED


def test_cancellation_from_pending() -> None:
    state = PaymentState.PENDING
    state = transition(state, PaymentState.CANCELLED)
    assert state == PaymentState.CANCELLED


def test_error_message_includes_states() -> None:
    with pytest.raises(InvalidTransitionError, match="PENDING -> SETTLED"):
        transition(PaymentState.PENDING, PaymentState.SETTLED)
