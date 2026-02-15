# Project structure

Canonical layout of the Data Tools repo. Use this as the single reference for where things live.

```
data tools/
├── .github/workflows/
│   ├── ci.yml              # CI: dbt deps/parse, Airflow DAG check, YAML lint
│   └── deploy.yml          # CD: deploy to dev/staging/prod via SSH
│
├── airflow/
│   ├── CONNECTIONS.md      # Airflow connections, troubleshooting
│   ├── dags/
│   │   ├── data_pipeline_lakehouse_dag.py   # Lakehouse: dbt against Dremio
│   │   ├── mysql_to_landing_dag.py          # MySQL → MinIO landing Parquet
│   │   ├── test_connections_dag.py          # Test mysql_source & Dremio
│   │   └── helpers/
│   │       └── mysql_to_landing.py          # Transfer logic (MySQL → Parquet)
│   └── logs/               # Airflow logs (gitignored)
│
├── dbt/
│   ├── README.md           # dbt usage and layer overview
│   ├── dbt_project.yml
│   ├── profiles.yml        # Dremio connection via env vars
│   ├── packages.yml
│   ├── models/
│   │   ├── README.md       # Model DAG
│   │   ├── sources.yml     # landing.plants, landing.licenses
│   │   ├── bronze/         # stg_* (staging from landing Parquet)
│   │   │   ├── schema.yml
│   │   │   ├── stg_plants.sql
│   │   │   └── stg_licenses.sql
│   │   ├── silver/         # dw_dim_* (data warehouse)
│   │   │   ├── schema.yml
│   │   │   ├── dw_dim_plant_profile.sql
│   │   │   └── dw_dim_date.sql
│   │   └── gold/           # dm_* (business marts)
│   │       ├── schema.yml
│   │       └── dm_plant.sql
│   └── tests/              # Singular dbt tests (DQ)
│
├── docs/
│   ├── PROJECT_STRUCTURE.md
│   ├── LAKEHOUSE.md
│   └── DEPLOYMENT.md
│
├── terraform/                 # IaC: deploy on Docker, AWS, GCP, or Azure
│   ├── README.md
│   └── environments/
│       ├── docker/            # Local/on-prem (Docker provider)
│       ├── aws/                # EC2 + Docker Compose
│       ├── gcp/                # GCE + Docker Compose
│       └── azure/              # Linux VM + Docker Compose
│
├── scripts/
│   ├── infra/
│   │   └── init-dbs.sh    # Create airflow + metabase DBs (when using docker-compose.postgres.yml)
│   ├── airflow/
│   │   ├── test_dag.sh    # Validate DAGs load
│   │   ├── test_connections.py
│   │   └── add_connections.sh
│   └── dbt/
│       ├── run.sh             # Run dbt via Airflow container (Dremio target)
│       └── run_lakehouse.sh   # Run dbt from host (Dremio target)
│
├── tests/
│   └── __init__.py
│
├── docker-compose.yml     # MinIO, Dremio, Airflow, MySQL, Metabase
├── docker-compose.dev.yml
├── docker-compose.staging.yml
├── docker-compose.prod.yml
├── docker-compose.postgres.yml   # Optional: Airflow metadata + Metabase on Postgres
├── Dockerfile.airflow
├── .env.example
├── .gitignore
└── README.md
```

## Where to change what

| Goal | Location |
|------|----------|
| Add or edit DAGs | `airflow/dags/` |
| Change MySQL→Landing logic | `airflow/dags/helpers/mysql_to_landing.py` |
| Add dbt models (bronze/silver/gold) | `dbt/models/` (correct layer folder) |
| Add dbt tests | `dbt/models/*/schema.yml` or `dbt/tests/` |
| Connection setup | `airflow/CONNECTIONS.md` |
| DB init (when using Postgres overlay) | `scripts/infra/init-dbs.sh` |
| Deploy stack | `docs/DEPLOYMENT.md`, `./scripts/deploy.sh`, `terraform/environments/` |
| CI/CD | `.github/workflows/ci.yml`, `deploy.yml` |
