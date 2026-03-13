# Fintech Labs

Interactive concept labs for fintech backend engineering. Each lab isolates one concept in the smallest runnable system that still contains it.

## Labs

| # | Lab | Concept | Status |
|---|-----|---------|--------|
| 01 | [Idempotent Payments](labs/01-idempotent-payments/) | Prevent duplicate charges | |
| 02 | [Webhook Processing](labs/02-webhook-processing/) | Verify and deduplicate payment events | |
| 03 | [Payment State Machine](labs/03-payment-state-machine/) | Enforce valid payment lifecycle | |

## Quick Start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Run all tests
pytest

# Open a lab notebook
marimo edit labs/01-idempotent-payments/lab.py
```

## Approach

Every lab follows the same pattern:
1. **Notebook** (`lab.py`) — First principles, failure demos, edge cases
2. **Code** (`app.py`) — Production-shaped extraction
3. **Tests** (`test_app.py`) — Edge cases that prove correctness
4. **CI** — Automated on every push
