# Terraform – Docker (local / on-prem)

Provisions the data stack as Docker containers on the machine where you run Terraform (same as Docker Compose).

**From repo root:**

```bash
terraform -chdir=terraform/environments/docker init
terraform -chdir=terraform/environments/docker apply
```

`project_root` defaults to the repo root (parent of `terraform/environments/docker`). Copy `terraform.tfvars.example` to `terraform.tfvars` to set passwords and options.
