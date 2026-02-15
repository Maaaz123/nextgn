output "landing_bucket" {
  description = "Landing bucket name (raw drops)"
  value       = aws_s3_bucket.landing.id
}

output "bronze_bucket" {
  description = "Bronze bucket name (raw parquet)"
  value       = aws_s3_bucket.bronze.id
}

output "silver_bucket" {
  description = "Silver bucket name (cleaned / conformed)"
  value       = aws_s3_bucket.silver.id
}

output "gold_bucket" {
  description = "Gold bucket name (marts)"
  value       = aws_s3_bucket.gold.id
}

output "logs_bucket" {
  description = "Logs bucket name (airflow logs, dbt artifacts)"
  value       = aws_s3_bucket.logs.id
}

output "bucket_names" {
  description = "All datalake bucket names"
  value = {
    landing = aws_s3_bucket.landing.id
    bronze  = aws_s3_bucket.bronze.id
    silver  = aws_s3_bucket.silver.id
    gold    = aws_s3_bucket.gold.id
    logs    = aws_s3_bucket.logs.id
  }
}
