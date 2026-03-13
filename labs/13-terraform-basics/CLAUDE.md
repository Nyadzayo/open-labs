# labs/13-terraform-basics/ — Terraform Basics

**Purpose:** Infrastructure as code for fintech services using Docker provider.

## Depends on
- Terraform CLI (optional — tests skip if not installed)

## Key files
- main.tf: Docker provider, network, Postgres container
- variables.tf: Configurable inputs with defaults
- outputs.tf: Connection string and container info
- test_terraform.py: Validation tests (skip gracefully without terraform)

## Test
`pytest labs/13-terraform-basics/ -v`
