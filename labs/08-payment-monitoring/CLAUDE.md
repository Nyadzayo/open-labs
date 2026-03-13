# labs/08-payment-monitoring/ — Payment Service Monitoring

**Purpose:** Instrument a payment API with Prometheus metrics, structured logging, and observability.

## Depends on
- Nothing (standalone lab)

## Key files
- app.py: FastAPI with /metrics endpoint and metrics middleware
- metrics.py: Prometheus Counter and Histogram definitions
- test_app.py: 5 tests verifying metrics exposure
- prometheus.yml: Scrape config
- docker-compose.yml: Prometheus + Grafana

## Test
`pytest labs/08-payment-monitoring/ -v`
