# labs/15-kyc-pipeline/ — KYC Document Pipeline

**Purpose:** Document intake + validation pipeline with state machine and audit trail.

## Depends on
- Nothing (standalone lab)

## Key files
- app.py: FastAPI with /documents (POST + GET)
- pipeline.py: validate_document function
- models.py: DocumentState enum + transition logic
- db.py: SQLite persistence
- test_pipeline.py: 12 validation + state machine tests
- test_app.py: 5 integration tests

## Test
`pytest labs/15-kyc-pipeline/ -v`
