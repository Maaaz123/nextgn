locals {
  # Repo root: run from repo root with terraform -chdir=terraform/environments/docker apply
  project_root = coalesce(var.project_root, abspath("${path.module}/../.."))
  postgres_conn = "postgresql+psycopg2://${var.postgres_user}:${var.postgres_password}@postgres:5432/airflow"
}
