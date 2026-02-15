# Datalake structure: landing, bronze, silver, gold, logs
# Creates buckets in MinIO (or S3-compatible storage)
# Run: terraform init && terraform plan && terraform apply
# Prerequisites: MinIO running (docker compose up -d minio)

module "datalake" {
  source = "../../modules/datalake"

  endpoint   = var.minio_endpoint
  access_key = var.minio_access_key
  secret_key = var.minio_secret_key

  bucket_prefix           = var.bucket_prefix
  create_placeholder_objects = var.create_placeholder_objects
}
