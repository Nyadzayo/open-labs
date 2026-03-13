# Lab 13: Terraform Basics

## Role Relevance
Platform Engineer — Infrastructure as code is standard. Terraform is the dominant tool.

## Business Problem
Dev sets up Postgres manually on their laptop. Works. Staging has a different version. Production has different networking. Nobody can reproduce any environment exactly.

## First Principles
- **Declarative**: Describe what you want, not how to get there
- **Plan**: Preview changes before applying
- **State**: Terraform tracks what it created so it knows what to update/delete
- **Providers**: Plugins that talk to AWS, Docker, Kubernetes, etc.

## How to Test
```bash
# If terraform installed:
pytest labs/13-terraform-basics/ -v

# Manual:
cd labs/13-terraform-basics
terraform init
terraform validate
terraform plan
terraform apply  # Creates Docker containers
terraform destroy  # Clean up
```

## What This Proves
"Managed fintech service infrastructure with Terraform, including CI validation."
