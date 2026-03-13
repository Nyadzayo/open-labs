# shared/ — Shared Test Infrastructure

**Purpose:** Reusable pytest fixtures and test helpers used across labs.

## Depends on
- None (this is the base module)

## Key files
- conftest.py: Shared fixtures (async client factory, temp DB)
- helpers.py: Test data factories and assertion helpers

## Test
`pytest shared/ -v` (no tests here — fixtures used by lab tests)
