output "landing_bucket" {
  value       = module.datalake.landing_bucket
  description = "Landing bucket (raw drops)"
}

output "bronze_bucket" {
  value       = module.datalake.bronze_bucket
  description = "Bronze bucket (raw parquet)"
}

output "silver_bucket" {
  value       = module.datalake.silver_bucket
  description = "Silver bucket (cleaned / conformed)"
}

output "gold_bucket" {
  value       = module.datalake.gold_bucket
  description = "Gold bucket (marts)"
}

output "logs_bucket" {
  value       = module.datalake.logs_bucket
  description = "Logs bucket (airflow logs, dbt artifacts)"
}

output "bucket_names" {
  value       = module.datalake.bucket_names
  description = "All datalake bucket names"
}
