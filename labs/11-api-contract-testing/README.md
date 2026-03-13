# Lab 11: API Contract Testing

## Role Relevance
Integration Engineer — every fintech integrates with external payment providers. Breaking changes = production outages.

## Business Problem
Payment provider removes a field from their API. Your code expects it. No contract test → production crash. With contract test → CI catches it before deploy.

## First Principles
- **Contract**: The agreed shape of API request/response
- **Breaking change**: Removing field, changing type, adding required field
- **Non-breaking change**: Adding optional field, adding new endpoint
- **Contract test**: Validate real responses against expected schema

## How to Test
```bash
pytest labs/11-api-contract-testing/ -v
```

## Edge Cases Covered
- Charge response matches contract
- Refund response matches contract
- Missing required field caught
- Wrong type caught
- Extra field from provider is safe
- Optional fields work

## What This Proves
"Built contract testing suite for payment provider API, catching schema drift before production."
