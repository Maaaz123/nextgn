# Gold Layer

Business data marts for analytics and BI.

## Models

| Model | Source | Description |
|-------|--------|-------------|
| `dm_plant` | dw_dim_plant_profile | Total plants by year, month, status, land provider, license status |

## Materialization

- Table
- Target: `minio.gold.*`
