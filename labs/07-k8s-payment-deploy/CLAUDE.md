# labs/07-k8s-payment-deploy/ — K8s Payment Service

**Purpose:** Deploy a payment API to Kubernetes with readiness/liveness probes and rolling updates.

## Depends on
- Nothing (standalone lab, but conceptually deploys a payment service like Lab 01)

## Key files
- app.py: FastAPI with /health/ready, /health/live, /payments
- test_app.py: 5 tests for probe endpoints
- Dockerfile: Multi-stage Python 3.12 build
- k8s/: Deployment, Service, Namespace manifests

## Test
`pytest labs/07-k8s-payment-deploy/ -v`
