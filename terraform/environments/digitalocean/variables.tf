variable "do_token" {
  description = "DigitalOcean API token (or set DIGITALOCEAN_TOKEN env var)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "region" {
  description = "DigitalOcean region (e.g. nyc1, sfo3, sgp1)"
  type        = string
  default     = "nyc1"
}

variable "project_name" {
  description = "Project name used for resource names"
  type        = string
  default     = "data-tools"
}

variable "droplet_size" {
  description = "Droplet size slug (e.g. s-2vcpu-4gb for 4GB RAM)"
  type        = string
  default     = "s-2vcpu-4gb"
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

variable "ssh_public_key_path" {
  description = "Path to SSH public key (e.g. ~/.ssh/id_rsa.pub)"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "allowed_cidr" {
  description = "CIDR allowed for SSH, Airflow, Metabase (0.0.0.0/0 = anywhere)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
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
