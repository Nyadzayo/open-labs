# labs/11-api-contract-testing/ — API Contract Testing

**Purpose:** Catch breaking provider API changes before production.

## Depends on
- Nothing (standalone lab with its own fake provider)

## Key files
- schemas.py: Pydantic contracts (ChargeResponse, RefundResponse)
- provider.py: Fake payment provider (FastAPI)
- client.py: ProviderClient that validates responses
- test_contracts.py: 7 contract tests including breaking change detection

## Test
`pytest labs/11-api-contract-testing/ -v`
