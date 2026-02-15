# Datalake structure: landing → bronze → silver → gold + logs
# Compatible with MinIO (S3 API), AWS S3, and other S3-compatible storage

provider "aws" {
  region = "us-east-1"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_region_validation      = true
  skip_requesting_account_id  = true

  access_key = var.access_key
  secret_key = var.secret_key

  endpoints {
    s3 = var.endpoint
  }

  # Path-style URLs for MinIO (required for non-AWS S3)
  s3_use_path_style = true
}

locals {
  prefix = var.bucket_prefix
}

# -----------------------------------------------------------------------------
# Buckets (layers)
# -----------------------------------------------------------------------------

# MinIO does not fully support PutBucketTagging or PutPublicAccessBlock.
# Buckets are private by default; no tags or public-access-block for MinIO compatibility.

resource "aws_s3_bucket" "landing" {
  bucket = "${local.prefix}landing"
}

resource "aws_s3_bucket" "bronze" {
  bucket = "${local.prefix}bronze"
}

resource "aws_s3_bucket" "silver" {
  bucket = "${local.prefix}silver"
}

resource "aws_s3_bucket" "gold" {
  bucket = "${local.prefix}gold"
}

resource "aws_s3_bucket" "logs" {
  bucket = "${local.prefix}logs"
}

# -----------------------------------------------------------------------------
# Placeholder objects (optional) – ensures folders exist
# -----------------------------------------------------------------------------

resource "aws_s3_object" "landing_keep" {
  count  = var.create_placeholder_objects ? 1 : 0
  bucket = aws_s3_bucket.landing.id
  key    = ".keep"
  content = "Landing zone - raw data drops"
  etag   = md5("Landing zone - raw data drops")
}

resource "aws_s3_object" "bronze_keep" {
  count  = var.create_placeholder_objects ? 1 : 0
  bucket = aws_s3_bucket.bronze.id
  key    = ".keep"
  content = "Bronze layer - raw parquet"
  etag   = md5("Bronze layer - raw parquet")
}

resource "aws_s3_object" "silver_keep" {
  count  = var.create_placeholder_objects ? 1 : 0
  bucket = aws_s3_bucket.silver.id
  key    = ".keep"
  content = "Silver layer - cleaned / conformed"
  etag   = md5("Silver layer - cleaned / conformed")
}

resource "aws_s3_object" "gold_keep" {
  count  = var.create_placeholder_objects ? 1 : 0
  bucket = aws_s3_bucket.gold.id
  key    = ".keep"
  content = "Gold layer - data marts"
  etag   = md5("Gold layer - data marts")
}

resource "aws_s3_object" "logs_keep" {
  count  = var.create_placeholder_objects ? 1 : 0
  bucket = aws_s3_bucket.logs.id
  key    = ".keep"
  content = "Logs - Airflow logs, dbt artifacts"
  etag   = md5("Logs - Airflow logs, dbt artifacts")
}
