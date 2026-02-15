# Datalake Structure (Terraform)

Creates the datalake bucket structure in MinIO (or S3-compatible storage):

| Bucket | Layer | Purpose |
|--------|-------|---------|
| `landing` | Landing | Raw drops – initial data ingestion |
| `bronze` | Bronze | Raw parquet – schema-on-read |
| `silver` | Silver | Cleaned / conformed – validated data |
| `gold` | Gold | Marts – business aggregates |
| `logs` | Logs | Airflow logs, dbt artifacts |

## Prerequisites

- MinIO running: `docker compose up -d minio`
- Terraform >= 1.0

## Usage

```bash
cd terraform/environments/datalake

# Copy and edit variables
cp terraform.tfvars.example terraform.tfvars

# Initialize and apply
terraform init
terraform plan
terraform apply
```

## Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `minio_endpoint` | MinIO URL | `http://localhost:9000` |
| `minio_access_key` | Access key | `minioadmin` |
| `minio_secret_key` | Secret key | `minioadmin` |
| `bucket_prefix` | Prefix for bucket names | `""` |
| `create_placeholder_objects` | Add .keep files | `true` |

## AWS / GCP / Azure

For cloud deployment, use the same module with the appropriate endpoint and credentials (S3, GCS, or Azure Blob). The module uses the AWS provider with a custom endpoint, which works with MinIO and any S3-compatible storage.
