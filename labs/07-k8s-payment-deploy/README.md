# Lab 07: K8s Payment Service Deployment

## Role Relevance
Platform Engineer / Backend with DevOps — K8s missing from 61/75 fintech listings. Having actual manifests with probes is concrete proof.

## Business Problem
Deploy payment service update → pods restart → requests hit unready pods → customers see 503 → lost payments.

## First Principles
- **Liveness probe**: Is the process alive? If not, restart it.
- **Readiness probe**: Can it handle traffic? If not, remove from load balancer.
- **Rolling update**: Replace pods one at a time, only send traffic to ready ones.

## How to Test
```bash
pytest labs/07-k8s-payment-deploy/ -v
```

## How to Deploy (with kind)
```bash
kind create cluster
docker build -t payment-api:latest labs/07-k8s-payment-deploy/
kind load docker-image payment-api:latest
kubectl apply -f labs/07-k8s-payment-deploy/k8s/
kubectl -n fintech-lab rollout status deployment/payment-api
```

## Edge Cases Covered
- Liveness returns 200 always
- Readiness returns 503 before startup
- Readiness returns 200 after startup
- Payment endpoint works through probes
- Root shows uptime

## What This Proves
"Deployed payment API to Kubernetes with readiness/liveness probes and rolling update strategy."
