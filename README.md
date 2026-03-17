# Fintech Labs

Interactive concept labs for fintech backend engineering. Each lab isolates one concept in the smallest runnable system that still contains it.

## Labs

| # | Lab | Concept |
|---|-----|---------|
| 01 | [Idempotent Payments](labs/01-idempotent-payments/) | Prevent duplicate charges with idempotency keys |
| 02 | [Webhook Processing](labs/02-webhook-processing/) | HMAC verification and event deduplication |
| 03 | [Payment State Machine](labs/03-payment-state-machine/) | Enforce valid payment lifecycle transitions |
| 04 | [Ledger Invariants](labs/04-ledger-invariants/) | Double-entry bookkeeping with balance invariants |
| 05 | [Reconciliation Engine](labs/05-reconciliation-engine/) | Match internal records against external provider |
| 06 | [Retry Patterns](labs/06-retry-patterns/) | Exponential backoff and circuit breaker |
| 07 | [K8s Payment Deploy](labs/07-k8s-payment-deploy/) | Containerize and deploy a payment service |
| 08 | [Payment Monitoring](labs/08-payment-monitoring/) | Prometheus metrics and observability |
| 09 | [Async Settlement](labs/09-async-settlement/) | Settlement queue with retry and dead-letter |
| 10 | [Event-Driven Payments](labs/10-event-driven-payments/) | Event sourcing with CQRS read model |
| 11 | [API Contract Testing](labs/11-api-contract-testing/) | Provider/consumer contract verification |
| 12 | [Rate Limiter](labs/12-rate-limiter/) | Token bucket and sliding window rate limiting |
| 13 | [Terraform Basics](labs/13-terraform-basics/) | Infrastructure as code for payment infra |
| 14 | [Fraud Rule Engine](labs/14-fraud-rule-engine/) | Configurable transaction risk scoring |
| 15 | [KYC Pipeline](labs/15-kyc-pipeline/) | Know Your Customer verification workflow |

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

## Structure

Every lab follows the same pattern:
1. **Notebook** (`lab.py`) — First principles exploration with [marimo](https://marimo.io)
2. **Code** — Production-shaped implementation (e.g. `app.py`, `ledger.py`, `rule_engine.py`)
3. **Tests** — Edge cases that prove correctness (148 tests across all labs)
4. **CI** — pytest, ruff, and mypy on every push

```
labs/
├── 01-idempotent-payments/
│   ├── lab.py           # marimo notebook
│   ├── app.py           # FastAPI payment service
│   ├── db.py            # SQLite storage
│   ├── test_payments.py # tests
│   ├── conftest.py      # test isolation
│   └── README.md
├── 02-webhook-processing/
│   └── ...
└── 15-kyc-pipeline/
    └── ...
```

## Tech Stack

- **Python 3.12+** with type annotations
- **FastAPI** for HTTP services
- **SQLite / aiosqlite** for storage
- **marimo** for interactive notebooks
- **pytest** + pytest-asyncio for testing
- **Prometheus** client for metrics (Lab 08)
- **Pydantic** for data validation
