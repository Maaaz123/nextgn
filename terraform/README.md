# Terraform – deploy on any infra

This folder contains **environment-specific** Terraform configs. The same data stack (Postgres + Airflow + dbt + Metabase) runs via **Docker Compose** everywhere; Terraform either runs that stack locally (Docker provider) or provisions a **VM on a cloud** and runs Compose there.

| Environment | Path | What it does |
|-------------|------|----------------|
| **Docker (local/on-prem)** | [environments/docker](environments/docker/) | Creates containers on your machine (same as `docker compose up`) |
| **AWS** | [environments/aws](environments/aws/) | EC2 + Docker + optional clone & run Compose |
| **GCP** | [environments/gcp](environments/gcp/) | GCE + Docker + optional clone & run Compose |
| **Azure** | [environments/azure](environments/azure/) | Linux VM + Docker + optional clone & run Compose |

**Run from the repo root**, for example:

```bash
# Local stack with Terraform
terraform -chdir=terraform/environments/docker init && terraform -chdir=terraform/environments/docker apply

# AWS
terraform -chdir=terraform/environments/aws init && terraform -chdir=terraform/environments/aws apply

# GCP (set TF_VAR_project_id or use tfvars)
terraform -chdir=terraform/environments/gcp init && terraform -chdir=terraform/environments/gcp apply

# Azure (set subscription_id)
terraform -chdir=terraform/environments/azure init && terraform -chdir=terraform/environments/azure apply
```

Or use the deploy script from repo root: **`./scripts/deploy.sh <docker|terraform|aws|gcp|azure>`**.

Full deployment guide: **[docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md)**.
