# Bronze Layer

Staging models that read from **landing** (Parquet in MinIO) and output to **Iceberg** tables.

## Models

| Model | Source | Description |
|-------|--------|-------------|
| `stg_plants` | landing.plants | Plants, deduped by `updated_at` |
| `stg_licenses` | landing.licenses | Licenses, deduped by `updated_at` |

## Materialization

- Incremental (merge on unique key)
- Target: `minio.bronze.*`
