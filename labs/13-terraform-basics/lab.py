"""Lab 13: Terraform Basics — marimo notebook."""

import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # Lab 13: Terraform Basics

        **Role relevance:** Platform Engineer / Backend Engineer — every production fintech
        service runs on infrastructure that must be reproducible, auditable, and version-controlled.
        Terraform is the dominant tool for this.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## 1. Why Infrastructure as Code?

        **The snowflake server problem:**

        A dev manually installs Postgres on their laptop. It works. They SSH into staging and
        run a slightly different set of commands. Works too — mostly. Production was set up
        six months ago by someone who left. Nobody knows exactly what's running.

        Now there's a bug that only reproduces in production. You can't replicate the
        environment. You're debugging blind.

        **IaC solves this:**

        - Configuration lives in git — every change is tracked, reviewed, reverted if needed
        - Environments are provisioned identically every time from the same source
        - `terraform apply` in staging and production run the exact same code
        - New team member? `git clone` + `terraform apply`. Done.

        **Fintech stakes are higher:**

        In payments, "works on my machine" costs money. An incorrectly configured database
        can mean data loss, compliance violations, or settlement failures. Reproducible
        infrastructure is not a luxury — it's a control.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## 2. Core Terraform Concepts

        ### Providers
        Plugins that let Terraform talk to external APIs. AWS, GCP, Azure, Kubernetes,
        Docker, Datadog — each is a provider. Providers declare what resource types exist.

        ```hcl
        terraform {
          required_providers {
            docker = {
              source  = "kreuzwerker/docker"
              version = "~> 3.0"
            }
          }
        }
        ```

        ### Resources
        The thing you want to exist. A container, a database, a VPC, a DNS record.
        Terraform creates, updates, or destroys resources to match your config.

        ```hcl
        resource "docker_container" "postgres" {
          name  = "fintech-postgres"
          image = docker_image.postgres.image_id
        }
        ```

        ### State
        Terraform writes a `terraform.tfstate` file after every apply. It records what
        Terraform created. On the next `plan`, Terraform reads state to calculate the
        diff between reality and your config.

        **Without state**: Terraform doesn't know what it created, can't update or delete it.

        ### Variables and Outputs
        Variables parameterise configs so the same code works for dev/staging/prod.
        Outputs expose values (like a connection string) after apply.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## 3. HCL Syntax Basics

        HCL (HashiCorp Configuration Language) is declarative — you describe the end state,
        not the steps to get there.

        ### Variables

        ```hcl
        variable "db_password" {
          description = "Database password"
          type        = string
          default     = "localdev"
          sensitive   = true   # Never printed in logs or plan output
        }
        ```

        ### Resource blocks

        ```hcl
        resource "<provider>_<type>" "<local_name>" {
          argument = value
          argument = var.some_variable   # Reference a variable
        }
        ```

        ### Referencing resources

        ```hcl
        # Format: <resource_type>.<local_name>.<attribute>
        image = docker_image.postgres.image_id
        name  = docker_network.fintech.name
        ```

        ### String interpolation

        ```hcl
        value = "postgresql://${var.db_user}:${var.db_password}@localhost:${var.db_port}/${var.db_name}"
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## 4. Docker Provider — Local Infrastructure Without Cloud Accounts

        The Docker provider provisions containers on your local Docker daemon. This is
        ideal for learning — no AWS account, no billing surprises, no IAM rabbit holes.

        Our config provisions:
        - A Docker network for isolation (`docker_network.fintech`)
        - A Postgres image pull (`docker_image.postgres`)
        - A Postgres container with environment variables and port mapping (`docker_container.postgres`)

        ```hcl
        resource "docker_container" "postgres" {
          name  = var.container_name
          image = docker_image.postgres.image_id

          env = [
            "POSTGRES_DB=${var.db_name}",
            "POSTGRES_USER=${var.db_user}",
            "POSTGRES_PASSWORD=${var.db_password}",
          ]

          ports {
            internal = 5432
            external = var.db_port
          }

          networks_advanced {
            name = docker_network.fintech.name
          }
        }
        ```

        **Why network isolation matters in fintech:** Payment services should not share
        a network namespace with public-facing services. Network segmentation is a
        security control. Terraform makes it declarative and auditable.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## 5. State Management

        `terraform.tfstate` is a JSON file that records everything Terraform manages:
        resource IDs, attributes, dependencies. Think of it as Terraform's memory.

        ### What state tracks:

        ```json
        {
          "resources": [
            {
              "type": "docker_container",
              "name": "postgres",
              "instances": [{
                "attributes": {
                  "id": "abc123",
                  "name": "fintech-postgres",
                  "image": "sha256:..."
                }
              }]
            }
          ]
        }
        ```

        ### Why state matters in fintech:

        | Scenario | Without state | With state |
        |----------|--------------|------------|
        | Re-run apply | Creates duplicate container | No-op, already exists |
        | Change port | Creates new container | Updates existing |
        | `destroy` | Can't find what to delete | Deletes exactly what it created |

        ### Remote state for teams:
        In production, state lives in S3 + DynamoDB (for locking), not a local file.
        Multiple engineers can apply changes without racing each other.

        **Never commit `terraform.tfstate` to git** — it contains secrets (passwords,
        connection strings). It's in `.gitignore` for this reason.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## 6. Plan vs Apply — Preview Before You Change

        `terraform plan` shows exactly what Terraform will do without doing it.
        This is the safety mechanism that makes IaC safe to use in production.

        ```
        $ terraform plan

        Terraform will perform the following actions:

          # docker_container.postgres will be created
          + resource "docker_container" "postgres" {
              + name  = "fintech-postgres"
              + image = "sha256:abc123..."
              + env   = [
                  + "POSTGRES_DB=payments",
                  + "POSTGRES_USER=fintech",
                  + "POSTGRES_PASSWORD=(sensitive value)",
                ]
            }

        Plan: 3 to add, 0 to change, 0 to destroy.
        ```

        ### The fintech workflow:

        1. Engineer writes Terraform change in a branch
        2. CI runs `terraform plan` and posts the diff to the PR
        3. Reviewer sees exactly what will change — no surprises
        4. Merge triggers `terraform apply` in staging
        5. After verification, apply in production

        **`terraform destroy`** is the nuclear option — removes everything Terraform
        manages. Useful for cleaning up dev environments. Never run in production
        without a plan review.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## 7. Fintech Relevance

        ### Reproducible database environments

        Every developer gets an identical Postgres instance with the same version,
        same config, same schema — provisioned in one command. No more "works on
        my machine" database bugs.

        ### Network isolation

        Payment services live on their own Docker network, isolated from other
        containers. Database port is not exposed to the host in production configs.
        This is PCI-DSS alignment by default.

        ### Secrets management

        Sensitive variables (`sensitive = true`) are never printed in plan output
        or logs. In production, these come from Vault, AWS Secrets Manager, or
        environment variables — never hardcoded.

        ### Auditability

        Every infrastructure change is a git commit. Who changed the database port?
        `git log variables.tf`. When did we upgrade Postgres? `git log main.tf`.
        This is an audit trail — required for SOC2 and PCI compliance.

        ### The interview answer:

        > "We used Terraform with the Docker provider locally and AWS provider in
        > production. All infrastructure changes went through PR review with
        > `terraform plan` output posted to the PR. State was stored in S3 with
        > DynamoDB locking. Sensitive values came from AWS Secrets Manager via
        > the `aws_secretsmanager_secret_version` data source."
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## 8. Hands-On Workflow

        ```bash
        cd labs/13-terraform-basics

        # Download the Docker provider plugin
        terraform init

        # Preview what will be created
        terraform plan

        # Create the containers (requires Docker running)
        terraform apply

        # Verify
        docker ps | grep fintech

        # Connect to the database
        psql postgresql://fintech:localdev@localhost:5432/payments

        # Clean up
        terraform destroy
        ```

        ### Override variables without editing files:

        ```bash
        terraform apply -var="db_port=5433" -var="container_name=payments-db"
        ```

        ### Use a tfvars file for environment-specific config:

        ```hcl
        # staging.tfvars
        db_port        = 5433
        container_name = "staging-postgres"
        db_password    = "staging-secret"
        ```

        ```bash
        terraform apply -var-file="staging.tfvars"
        ```
        """
    )
    return


@app.cell
def _(mo):
    confidence = mo.ui.slider(1, 10, value=7, label="Confidence: I can write Terraform configs and explain IaC to an interviewer")
    return (confidence,)


@app.cell
def _(confidence, mo):
    mo.md(
        f"""
        ## Reflection

        **Confidence score:** {confidence.value}/10

        ### What this lab proves:
        - You can write valid HCL with variables, resources, and outputs
        - You understand providers, state, and plan/apply lifecycle
        - You can explain why IaC matters in a fintech context (reproducibility, audit trail, compliance)

        ### Resume line:
        > "Managed fintech service infrastructure with Terraform, including CI validation
        > and Docker provider for local reproducible environments."

        ### Next steps if confidence < 7:
        - Run `terraform init && terraform plan` manually — read the output carefully
        - Change `db_port` to 5433 in variables.tf, re-run plan, see what changes
        - Add a second container (Redis) to main.tf — practice the resource block pattern

        ### Next steps if confidence >= 7:
        - Lab 14: Fraud Rule Engine — apply what you know about reproducible infra
        - Extend this config to use AWS provider (RDS instead of Docker container)
        - Add a `data` source to reference an existing network instead of creating one
        """
    )
    return


if __name__ == "__main__":
    app.run()
