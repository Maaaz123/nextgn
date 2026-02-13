output "airflow_url" {
  description = "Airflow webserver URL"
  value       = "http://localhost:${var.airflow_port}"
}

output "metabase_url" {
  description = "Metabase URL"
  value       = "http://localhost:${var.metabase_port}"
}

output "postgres_port" {
  description = "Postgres host port"
  value       = var.postgres_port
}

output "project_root" {
  description = "Project root path used for bind mounts"
  value       = local.project_root
}
