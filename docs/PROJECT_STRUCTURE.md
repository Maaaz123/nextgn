# Project structure

Canonical layout of the Data Tools repo. Use this as the single reference for where things live.

```
data tools/
├── .github/workflows/
│   ├── ci.yml              # CI: dbt compile/run/test, Airflow DAG check, YAML lint
│   └── deploy.yml          # CD: deploy to dev/staging/prod via SSH
│
├── airflow/
│   ├── CONNECTIONS.md      # Airflow connections, variables, troubleshooting
│   ├── dags/
│   │   ├── data_pipeline_dag.py   # Full pipeline: ingest → dbt (bronze→silver→gold)
│   │   ├── dbt_dag.py             # dbt deps / run / test only
│   │   ├── mysql_to_postgres_dag.py  # MySQL → Postgres raw sync
│   │   ├── test_connections_dag.py   # Test mysql_source & postgres_warehouse
│   │   └── helpers/
│   │       └── mysql_to_postgres.py  # Transfer logic (batching, state, incremental)
│   └── logs/               # Airflow logs (gitignored)
│
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml        # Warehouse connection via env vars
│   ├── packages.yml
│   ├── models/
│   │   ├── sources.yml     # raw.flows, raw.plants, raw.licenses
│   │   ├── schema.yml     # Tests (unique, not_null, etc.)
│   │   ├── bronze/        # dl_* (data lake views on raw)
│   │   ├── stg/           # stg_* (transformations)
│   │   ├── silver/        # dw_fact_*, dw_dim_* (data warehouse)
│   │   └── gold/          # dm_* (business marts)
│   └── tests/             # Singular dbt tests (DQ)
│
├── docs/
│   └── PROJECT_STRUCTURE.md   # This file
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
│   │   └── init-dbs.sh    # Postgres: create warehouse, airflow, metabase DBs + raw schema
│   ├── airflow/
│   │   ├── test_dag.sh    # Validate DAGs load (list-import-errors)
│   │   ├── test_connections.py
│   │   └── generate_mysql_postgres_variable.py
│   ├── db/
│   │   └── verify_postgres_raw.sh   # List raw tables and row counts
│   └── dbt/
│       └── run.sh                    # Run dbt via Docker (no local dbt install)
│
├── tests/
│   └── test_mysql_to_postgres.py   # Pytest for mysql_to_postgres helper
│
├── docker-compose.yml     # Postgres, Airflow, Metabase (optional MySQL)
├── docker-compose.dev.yml
├── docker-compose.staging.yml
├── docker-compose.prod.yml
├── Dockerfile.airflow     # Airflow image + dbt-core, dbt-postgres
├── .env.example
├── .gitignore
└── README.md
```

## Where to change what

| Goal | Location |
|------|----------|
| Add or edit DAGs | `airflow/dags/` |
| Change MySQL→Postgres logic | `airflow/dags/helpers/mysql_to_postgres.py` |
| Add dbt models (bronze/stg/silver/gold) | `dbt/models/` (correct layer folder) |
| Add dbt tests | `dbt/models/schema.yml` or `dbt/tests/` |
| Connection and variable setup | `airflow/CONNECTIONS.md` |
| DB init (new DBs, raw schema) | `scripts/infra/init-dbs.sh` |
| Deploy stack (any infra) | `docs/DEPLOYMENT.md`, `./scripts/deploy.sh`, `terraform/environments/{docker,aws,gcp,azure}` |
| CI/CD | `.github/workflows/ci.yml`, `deploy.yml` |
