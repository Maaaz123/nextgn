# Silver Layer

Data warehouse dimension and fact tables.

## Models

| Model | Sources | Description |
|-------|---------|-------------|
| `dw_dim_plant_profile` | stg_plants, stg_licenses | Plant + license attributes (joined) |
| `dw_dim_date` | – | Date dimension (spine 2010–2030) |

## Materialization

- Table
- Target: `minio.silver.*`
