# Lab 15: KYC Document Pipeline

## Role Relevance
Fintech Backend / Compliance Engineering — KYC is mandatory for every financial services company.

## Business Problem
Customer uploads ID document. It needs validation: correct format, within size limits, readable. Invalid docs → rejected with reason. Valid docs → approved. Everything audited.

## First Principles
- **Pipeline**: Sequential processing stages (upload → validate → decide)
- **State machine**: Document moves through defined states with enforced transitions
- **Audit trail**: Every state change is recorded with timestamp and reason

## How to Test
```bash
pytest labs/15-kyc-pipeline/ -v
```

## Edge Cases Covered
- Valid PDF/JPEG/PNG documents approved
- Unsupported file types rejected
- Empty files rejected
- Oversized files rejected
- Missing filename rejected
- Document status queryable by ID
- 404 for nonexistent documents
- Can't skip validation (UPLOADED → APPROVED blocked)
- Can re-upload after rejection

## What This Proves
"Built KYC document pipeline with async validation and compliance-ready audit trail."
