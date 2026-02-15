variable "project_root" {
  description = "Absolute path to the project root (for bind mounts). Defaults to repo root."
  type        = string
  default     = ""
}

variable "postgres_user" {
  description = "PostgreSQL user"
  type        = string
  default     = "postgres"
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "airflow_username" {
  description = "Airflow webserver admin username"
  type        = string
  default     = "admin"
}

variable "airflow_password" {
  description = "Airflow webserver admin password"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "enable_mysql" {
  description = "Create optional MySQL container for mysql_to_landing DAG"
  type        = bool
  default     = false
}

variable "postgres_port" {
  description = "Host port for Postgres"
  type        = number
  default     = 5432
}

variable "airflow_port" {
  description = "Host port for Airflow webserver"
  type        = number
  default     = 8080
}

variable "metabase_port" {
  description = "Host port for Metabase"
  type        = number
  default     = 3000
}
