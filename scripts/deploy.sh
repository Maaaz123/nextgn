#!/usr/bin/env bash
# Deploy the data stack: local (Docker Compose or Terraform Docker), AWS, GCP, or Azure.
# Usage: ./scripts/deploy.sh <target>
#   target: docker | terraform | datalake | aws | gcp | azure
# Run from project root. For cloud targets, set variables (e.g. terraform.tfvars) first.

set -e
TARGET="${1:-}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

case "$TARGET" in
  docker)
    echo "=== Deploying with Docker Compose ==="
    docker compose up -d
    echo "Airflow: http://localhost:8080  Metabase: http://localhost:3000"
    ;;
  terraform)
    echo "=== Deploying with Terraform (Docker) ==="
    terraform -chdir=terraform/environments/docker init -input=false
    terraform -chdir=terraform/environments/docker apply -input=false
    terraform -chdir=terraform/environments/docker output
    ;;
  aws)
    echo "=== Deploying to AWS (Terraform) ==="
    terraform -chdir=terraform/environments/aws init -input=false
    terraform -chdir=terraform/environments/aws apply -input=false
    terraform -chdir=terraform/environments/aws output
    ;;
  gcp)
    echo "=== Deploying to GCP (Terraform) ==="
    terraform -chdir=terraform/environments/gcp init -input=false
    terraform -chdir=terraform/environments/gcp apply -input=false
    terraform -chdir=terraform/environments/gcp output
    ;;
  azure)
    echo "=== Deploying to Azure (Terraform) ==="
    terraform -chdir=terraform/environments/azure init -input=false
    terraform -chdir=terraform/environments/azure apply -input=false
    terraform -chdir=terraform/environments/azure output
    ;;
  datalake)
    echo "=== Creating datalake buckets (MinIO) ==="
    echo "Prerequisites: docker compose up -d minio"
    terraform -chdir=terraform/environments/datalake init -input=false
    terraform -chdir=terraform/environments/datalake apply -input=false \
      -var="minio_endpoint=http://localhost:9000" \
      -var="minio_access_key=minioadmin" \
      -var="minio_secret_key=minioadmin"
    terraform -chdir=terraform/environments/datalake output
    ;;
  *)
    echo "Usage: $0 <target>"
    echo "  target: docker | terraform | datalake | aws | gcp | azure"
    echo "  docker    - docker compose up -d"
    echo "  terraform - Terraform Docker (local)"
    echo "  datalake  - Create landing, bronze, silver, gold, logs buckets in MinIO"
    echo "  aws       - Terraform → EC2 + Docker"
    echo "  gcp       - Terraform → GCE + Docker"
    echo "  azure     - Terraform → Azure VM + Docker"
    echo "See docs/DEPLOYMENT.md for variables and details."
    exit 1
    ;;
esac
