"""Prometheus metrics for payment service."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

PAYMENT_CREATED = Counter(
    "payment_created_total",
    "Total payments created",
    ["status", "currency"],
)

PAYMENT_LATENCY = Histogram(
    "payment_latency_seconds",
    "Payment processing latency",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

WEBHOOK_RECEIVED = Counter(
    "webhook_received_total",
    "Total webhooks received",
    ["event_type", "valid"],
)
