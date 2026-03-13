# labs/03-payment-state-machine/ — Payment State Machine

**Purpose:** Enforce valid payment lifecycle transitions with explicit state definitions.

## Depends on
- None

## Key files
- lab.py: marimo notebook — state machine concepts, visual transition diagram
- state_machine.py: PaymentState enum, VALID_TRANSITIONS dict, transition function
- test_state_machine.py: 23 tests covering all valid/invalid transitions

## Key types
- PaymentState: Enum with PENDING, AUTHORIZED, CAPTURED, SETTLED, REFUNDED, CANCELLED, FAILED
- InvalidTransitionError: Raised on illegal transitions

## Test
`pytest labs/03-payment-state-machine/ -v`
