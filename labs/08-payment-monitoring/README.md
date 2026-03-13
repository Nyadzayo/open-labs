# Lab 08: Payment Service Monitoring

## Role Relevance
Backend Engineer / SRE — observability is a growing requirement. Most candidates can't demonstrate it.

## Business Problem
Payment latency spikes from 100ms to 5s. Without monitoring: customers churn silently. With monitoring: alert fires, on-call investigates, fix deployed in minutes.

## First Principles
- **Counter**: How many payments? How many errors? (monotonically increasing)
- **Histogram**: How long do payments take? What's the p99 latency? (distribution)
- **Alerts**: When counters or latencies cross thresholds, notify humans.

## How to Test
```bash
pytest labs/08-payment-monitoring/ -v
```

## How to Run with Prometheus + Grafana
```bash
cd labs/08-payment-monitoring
uvicorn app:app --port 8000 &
docker compose up -d
# Prometheus at http://localhost:9090
# Grafana at http://localhost:3000 (admin/admin)
```

## Edge Cases Covered
- Metrics endpoint returns Prometheus text format
- Payment counter increments on each request
- Latency histogram records payment endpoint timing
- Health endpoint works alongside metrics

## What This Proves
"Instrumented payment API with Prometheus metrics, latency histograms, and Grafana dashboards."
