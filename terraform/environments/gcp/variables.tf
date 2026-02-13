variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "project_name" {
  description = "Project name for resource names"
  type        = string
  default     = "data-tools"
}

variable "machine_type" {
  description = "GCE machine type"
  type        = string
  default     = "e2-medium"
}

variable "repo_url" {
  description = "Git repo URL to clone and run Docker Compose"
  type        = string
  default     = ""
}

variable "repo_branch" {
  description = "Branch to clone"
  type        = string
  default     = "main"
}

variable "postgres_password" {
  description = "Postgres password for stack"
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "airflow_password" {
  description = "Airflow UI password"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "allowed_cidr" {
  description = "CIDR allowed to access (0.0.0.0/0 = anywhere)"
  type        = string
  default     = "0.0.0.0/0"
}
