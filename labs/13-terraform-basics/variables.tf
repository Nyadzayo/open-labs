variable "network_name" {
  description = "Docker network name"
  type        = string
  default     = "fintech-network"
}

variable "container_name" {
  description = "Postgres container name"
  type        = string
  default     = "fintech-postgres"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "payments"
}

variable "db_user" {
  description = "Database user"
  type        = string
  default     = "fintech"
}

variable "db_password" {
  description = "Database password"
  type        = string
  default     = "localdev"
  sensitive   = true
}

variable "db_port" {
  description = "External port for Postgres"
  type        = number
  default     = 5432
}
