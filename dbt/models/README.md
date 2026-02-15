# dbt Models

```
models/
├── sources.yml      # Landing (Parquet) and raw (Postgres) sources
├── bronze/          # stg_* – staging from landing
│   ├── schema.yml
│   ├── stg_plants.sql
│   └── stg_licenses.sql
├── silver/          # dw_dim_* – data warehouse dimensions
│   ├── schema.yml
│   ├── dw_dim_plant_profile.sql
│   └── dw_dim_date.sql
└── gold/            # dm_* – business marts
    ├── schema.yml
    └── dm_plant.sql
```

## DAG

```
landing (Parquet) → stg_plants ─┐
                                ├→ dw_dim_plant_profile → dm_plant
landing (Parquet) → stg_licenses─┘

(no source) → dw_dim_date
```
