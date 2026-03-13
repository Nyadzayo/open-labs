output "postgres_container_name" {
  description = "Name of the Postgres container"
  value       = docker_container.postgres.name
}

output "postgres_port" {
  description = "External port for Postgres"
  value       = var.db_port
}

output "connection_string" {
  description = "PostgreSQL connection string"
  value       = "postgresql://${var.db_user}:${var.db_password}@localhost:${var.db_port}/${var.db_name}"
  sensitive   = true
}
