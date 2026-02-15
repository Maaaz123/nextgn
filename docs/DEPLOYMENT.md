# Deploy the data stack anywhere

One stack (MinIO + Dremio + Airflow + dbt + Metabase), same Docker Compose. Deploy locally, on-prem, or on **AWS**, **GCP**, or **Azure** with the same commands and config.

## Quick reference

| Where | How | Command / link |
|-------|-----|----------------|
| **Local / on-prem** | Docker Compose | `docker compose up -d` |
| **Local (Terraform)** | Terraform Docker | From repo root: `terraform -chdir=terraform/environments/docker init && terraform -chdir=terraform/environments/docker apply` |
| **AWS** | Terraform → EC2 + Docker | `terraform -chdir=terraform/environments/aws init && terraform -chdir=terraform/environments/aws apply` |
| **GCP** | Terraform → GCE + Docker | `terraform -chdir=terraform/environments/gcp init && terraform -chdir=terraform/environments/gcp apply` |
| **Azure** | Terraform → Linux VM + Docker | `terraform -chdir=terraform/environments/azure init && terraform -chdir=terraform/environments/azure apply` |

All cloud options use the **same** `docker-compose.yml`: Terraform creates a VM, installs Docker and Compose, then clones your repo and runs `docker compose up -d`. So you only maintain one stack definition.

---

## 1. Local or on-prem (Docker only)

**Prerequisites:** Docker and Docker Compose.

```bash
cp .env.example .env
docker compose up -d
```

- Airflow: http://localhost:8080  
- Metabase: http://localhost:3000  

On **your own server** (on-prem): copy the repo, create `.env`, run the same. No cloud account needed.

---

## 2. Local with Terraform (Docker provider)

**Prerequisites:** Terraform, Docker.

From the **repo root**:

```bash
terraform -chdir=terraform/environments/docker init
terraform -chdir=terraform/environments/docker apply
```

Same stack as Compose, managed by Terraform (state, variables). See `terraform/environments/docker/README.md` for variables.

---

## 3. AWS (EC2)

**Prerequisites:** AWS CLI configured, Terraform, SSH key.

1. Copy and edit variables:
   ```bash
   cp terraform/environments/aws/terraform.tfvars.example terraform/environments/aws/terraform.tfvars
   # Set: repo_url (your Git URL), ssh_public_key_path, optionally postgres_password, airflow_password
   ```

2. Apply:
   ```bash
   terraform -chdir=terraform/environments/aws init
   terraform -chdir=terraform/environments/aws apply
   ```

3. After apply, Terraform outputs `airflow_url`, `metabase_url`, `public_ip`. If `repo_url` was set and the repo is **public**, the VM will have cloned and started the stack; wait 2–3 minutes then open the URLs. If the repo is **private**, SSH in and run:
   ```bash
   git clone <your-repo> app && cd app && cp .env.example .env && docker compose up -d
   ```

**Variables:** `terraform/environments/aws/variables.tf` — important: `repo_url`, `repo_branch`, `ssh_public_key_path`, `aws_region`, `allowed_cidr`.

---

## 4. GCP (Google Cloud)

**Prerequisites:** `gcloud` auth and a project, Terraform.

1. Set project and (optional) tfvars:
   ```bash
   export TF_VAR_project_id=your-gcp-project-id
   # Or: cp terraform/environments/gcp/terraform.tfvars.example terraform/environments/gcp/terraform.tfvars
   ```

2. Apply:
   ```bash
   terraform -chdir=terraform/environments/gcp init
   terraform -chdir=terraform/environments/gcp apply
   ```

3. Use outputs for Airflow and Metabase URLs. If `repo_url` is set (public repo), the instance will start the stack via startup script. Otherwise SSH (see output `ssh_command`) and run clone + `docker compose up -d`.

**Variables:** `project_id` (required), `region`, `zone`, `repo_url`, `repo_branch`, `postgres_password`, `airflow_password`, `allowed_cidr`.

---

## 5. Azure

**Prerequisites:** Azure CLI logged in, Terraform, SSH key.

1. Set subscription and (optional) tfvars:
   ```bash
   export ARM_SUBSCRIPTION_ID=your-subscription-id
   # Or use terraform.tfvars with subscription_id
   ```

2. Apply:
   ```bash
   terraform -chdir=terraform/environments/azure init
   terraform -chdir=terraform/environments/azure apply
   ```

3. Use outputs for URLs. If `repo_url` is set, the VM runs cloud-init and starts the stack; otherwise SSH and run clone + `docker compose up -d`.

**Variables:** `subscription_id` (required), `location`, `admin_ssh_public_key_path`, `repo_url`, `repo_branch`, `postgres_password`, `airflow_password`, `allowed_cidr`.

---

## Deploy script (optional)

From repo root:

```bash
./scripts/deploy.sh docker    # same as: docker compose up -d
./scripts/deploy.sh terraform # Terraform Docker env
./scripts/deploy.sh aws       # Terraform AWS
./scripts/deploy.sh gcp       # Terraform GCP
./scripts/deploy.sh azure     # Terraform Azure
```

The script only runs the right Terraform or Compose; set variables (e.g. tfvars or env) yourself before running.

---

## Summary

- **One stack:** same `docker-compose.yml` and app code everywhere.
- **Local / on-prem:** Docker Compose or Terraform Docker.
- **Cloud:** Terraform creates a VM, installs Docker, clones repo, runs `docker compose up -d`. Set `repo_url` (and secrets) per environment.
- **Security:** Use strong passwords in tfvars (or env), restrict `allowed_cidr` in production, use private repo + deploy keys if needed.
