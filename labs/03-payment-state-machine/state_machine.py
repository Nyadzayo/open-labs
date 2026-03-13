"""Payment state machine with enforced transitions.

Valid payment lifecycle:
  PENDING -> AUTHORIZED -> CAPTURED -> SETTLED
  PENDING -> CANCELLED
  AUTHORIZED -> CANCELLED
  AUTHORIZED -> FAILED
  CAPTURED -> REFUNDED
  CAPTURED -> SETTLED
"""

from __future__ import annotations

from enum import StrEnum


class PaymentState(StrEnum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    SETTLED = "SETTLED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


# Allowed transitions: from_state -> {set of valid to_states}
VALID_TRANSITIONS: dict[PaymentState, set[PaymentState]] = {
    PaymentState.PENDING: {PaymentState.AUTHORIZED, PaymentState.CANCELLED},
    PaymentState.AUTHORIZED: {
        PaymentState.CAPTURED,
        PaymentState.CANCELLED,
        PaymentState.FAILED,
    },
    PaymentState.CAPTURED: {PaymentState.SETTLED, PaymentState.REFUNDED},
    PaymentState.SETTLED: set(),
    PaymentState.REFUNDED: set(),
    PaymentState.CANCELLED: set(),
    PaymentState.FAILED: set(),
}


class InvalidTransitionError(Exception):
    """Raised when a payment transition is not allowed."""

    def __init__(self, from_state: PaymentState, to_state: PaymentState) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid transition: {from_state.value} -> {to_state.value}"
        )


def transition(current: PaymentState, target: PaymentState) -> PaymentState:
    """Transition a payment from current state to target state.

    Raises InvalidTransitionError if the transition is not allowed.
    """
    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidTransitionError(current, target)
    return target
