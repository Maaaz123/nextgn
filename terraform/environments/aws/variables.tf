variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource names"
  type        = string
  default     = "data-tools"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "repo_url" {
  description = "Git repo URL to clone and run Docker Compose (e.g. https://github.com/yourorg/data-tools.git)"
  type        = string
  default     = ""
}

variable "repo_branch" {
  description = "Branch to clone"
  type        = string
  default     = "main"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key for EC2 access (e.g. ~/.ssh/id_rsa.pub)"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "allowed_cidr" {
  description = "CIDR allowed to access SSH, Airflow, Metabase (0.0.0.0/0 = anywhere)"
  type        = string
  default     = "0.0.0.0/0"
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
