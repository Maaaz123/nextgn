variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "project_name" {
  description = "Project name for resource names"
  type        = string
  default     = "data-tools"
}

variable "vm_size" {
  description = "VM size"
  type        = string
  default     = "Standard_B2s"
}

variable "admin_username" {
  description = "VM admin username"
  type        = string
  default     = "azureuser"
}

variable "admin_ssh_public_key_path" {
  description = "Path to SSH public key (e.g. ~/.ssh/id_rsa.pub)"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
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
  description = "CIDR allowed (e.g. 0.0.0.0/0)"
  type        = string
  default     = "0.0.0.0/0"
}
