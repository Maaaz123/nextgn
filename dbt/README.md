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

## Tags (layer + domain)

Models are tagged by **layer** (in `dbt_project.yml`) and **domain** (in each model’s `schema.yml`):

| Tag | Use |
|-----|-----|
| `bronze`, `silver`, `gold` | Layer (folder-level) |
| `domain_plants`, `domain_licenses` | Business domain |
| `domain_shared` | Shared dimensions (e.g. dw_dim_date) |

Examples:

```bash
dbt run --select tag:bronze
dbt run --select tag:domain_plants
dbt run --select tag:domain_licenses,tag:domain_plants
```

## Config

- **Profiles**: `profiles.yml` (uses env vars for credentials)
- **Target**: `dremio_dev` (default)
- **Vars**: `dim_date_start`, `dim_date_end`, `environment` in `dbt_project.yml`
