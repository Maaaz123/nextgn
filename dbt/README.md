# dbt – Data Tools

Transformations for the data lakehouse: **landing → bronze → silver → gold**.

## Stack

- **Target**: Dremio (MinIO + Iceberg)
- **Adapter**: dbt-dremio

## Layers

| Layer | Path | Models |
|-------|------|--------|
| **Bronze** | `minio.bronze.*` | stg_plants, stg_licenses |
| **Silver** | `minio.silver.*` | dw_dim_plant_profile, dw_dim_date |
| **Gold** | `minio.gold.*` | dm_plant |

## Quick Start

```bash
# Install
pip install -r requirements-dbt.txt

# Run all models
dbt run

# Run specific model
dbt run -s dm_plant

# Test
dbt test
```

## Config

- **Profiles**: `profiles.yml` (uses env vars for credentials)
- **Target**: `dremio_dev` (default)
- **Vars**: `dim_date_start`, `dim_date_end` in `dbt_project.yml`
