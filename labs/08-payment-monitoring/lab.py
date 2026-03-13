"""Lab 08: Payment Service Monitoring — marimo notebook."""

import marimo

__generated_with = "0.9.0"
app = marimo.App(title="Lab 08: Payment Service Monitoring")


@app.cell
def __(mo):
    mo.md(
        """
        # Lab 08: Payment Service Monitoring

        **Role:** Backend Engineer / SRE
        **Tier:** 3 — Production Observability

        ---

        ## 1. WHY Monitoring Matters

        A payment fails silently at 2 AM. No alert fires. By morning, 500 customers have
        tried to pay and seen a blank error screen. Support tickets pile up. Revenue is lost.

        **Without monitoring:** you find out when customers complain — hours later.
        **With monitoring:** an alert fires within minutes, on-call gets paged, fix is deployed.

        > "You cannot improve what you cannot measure." — Peter Drucker
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
        ## 2. Metrics Types

        | Type | Use Case | Example |
        |------|----------|---------|
        | **Counter** | Totals that only go up | `payment_created_total` |
        | **Histogram** | Latency distribution, p50/p95/p99 | `payment_latency_seconds` |
        | **Gauge** | Current state, can go up or down | `active_connections` |
        | **Summary** | Like histogram, pre-calculated quantiles | Rarely used in modern stacks |

        ### Rule of thumb:
        - **Did something happen?** → Counter
        - **How long did it take?** → Histogram
        - **What is the current value?** → Gauge
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
        ## 3. Key Payment Metrics

        ```python
        # How many payments were created? (Counter)
        payment_created_total{status="PENDING", currency="USD"} 1042

        # How long do payments take? (Histogram — p99 latency)
        payment_latency_seconds_bucket{le="0.1"} 900
        payment_latency_seconds_bucket{le="0.5"} 1000
        payment_latency_seconds_bucket{le="1.0"} 1040
        payment_latency_seconds_bucket{le="+Inf"} 1042

        # How many webhooks arrived? (Counter with validity label)
        webhook_received_total{event_type="payment.completed", valid="true"} 980
        webhook_received_total{event_type="payment.completed", valid="false"} 62
        ```

        **Error rate formula (PromQL):**
        ```
        rate(payment_created_total{status="FAILED"}[5m])
        /
        rate(payment_created_total[5m])
        ```
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
        ## 4. Prometheus Pull Model

        Prometheus uses a **pull-based** model — it scrapes your `/metrics` endpoint
        on a schedule (default: 15 seconds).

        ```
        ┌─────────────┐     GET /metrics     ┌──────────────┐
        │  Prometheus  │ ──────────────────► │  Payment API  │
        │  (scraper)   │ ◄────────────────── │  :8000        │
        └─────────────┘   text/plain metrics └──────────────┘
               │
               ▼ store in TSDB
        ┌─────────────┐
        │   Grafana    │  query via PromQL
        └─────────────┘
        ```

        Your app exposes:
        ```
        GET /metrics  →  prometheus text format
        ```

        Prometheus config (`prometheus.yml`):
        ```yaml
        scrape_configs:
          - job_name: "payment-api"
            static_configs:
              - targets: ["host.docker.internal:8000"]
        ```
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
        ## 5. Alert Design

        A good alert answers: **"Is something broken that requires human action?"**

        ### Error Rate Alert (PagerDuty / Slack)
        ```yaml
        # alerting rule (Prometheus)
        - alert: PaymentErrorRateHigh
          expr: |
            rate(payment_created_total{status="FAILED"}[5m])
            / rate(payment_created_total[5m]) > 0.05
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Payment error rate > 5% for 5 minutes"
            runbook: "https://wiki/runbooks/payment-errors"
        ```

        ### Latency Alert
        ```yaml
        - alert: PaymentLatencyHigh
          expr: |
            histogram_quantile(0.99,
              rate(payment_latency_seconds_bucket[5m])
            ) > 2.0
          for: 2m
          labels:
            severity: warning
          annotations:
            summary: "p99 payment latency > 2s"
        ```

        **Alert fatigue:** Only alert on symptoms that need human intervention.
        Too many alerts = engineers ignore them.
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
        ## 6. Structured Logging

        Raw logs: `2024-01-15 ERROR payment failed`

        Structured logs (JSON with correlation IDs):
        ```json
        {
          "timestamp": "2024-01-15T10:23:45Z",
          "level": "ERROR",
          "service": "payment-api",
          "trace_id": "abc123",
          "payment_id": "pay_001",
          "amount": 99.99,
          "currency": "USD",
          "error": "card_declined",
          "duration_ms": 234
        }
        ```

        **Why correlation IDs matter:**
        - One payment request touches: API → auth → fraud → ledger → bank
        - `trace_id` links all log lines across services
        - Without it: finding a failed payment takes hours of grep

        **Python structured logging:**
        ```python
        import structlog
        log = structlog.get_logger()
        log.error("payment_failed",
                  payment_id="pay_001",
                  error="card_declined",
                  trace_id=request.headers.get("X-Trace-Id"))
        ```
        """
    )
    return


@app.cell
def __(mo):
    import marimo as mo

    confidence = mo.ui.slider(1, 10, value=7, label="Confidence score (1-10)")
    mo.md(f"## 7. Reflection\n\n{confidence}\n\n**Drag to rate your confidence in payment monitoring concepts.**")
    return confidence, mo


@app.cell
def __(confidence, mo):
    level_map = {
        (1, 3): ("Beginner", "Re-read sections 2-4 and implement the webhook counter."),
        (4, 6): ("Developing", "You have the basics. Add a Gauge metric and write a PromQL alert query."),
        (7, 8): ("Proficient", "Solid foundation. Next: add Grafana dashboard JSON and structured logging middleware."),
        (9, 10): ("Expert", "Strong grasp. Challenge: implement distributed tracing with OpenTelemetry."),
    }
    level, advice = next(
        (v for k, v in level_map.items() if k[0] <= confidence.value <= k[1]),
        ("Unknown", "")
    )
    mo.callout(
        mo.md(f"**Level: {level}**\n\n{advice}"),
        kind="info",
    )
    return advice, level, level_map


if __name__ == "__main__":
    app.run()
