# Data Tools Stack

Modern data stack: **MinIO + Apache Iceberg + Dremio** as the warehouse, **dbt** for transformations, **Airflow** for orchestration. No Postgres required (optional overlay adds it).

- **MinIO** – S3-compatible object storage (Iceberg data)
- **Dremio** – query engine for Iceberg tables
- **dbt Core** – SQL transformations (dbt-dremio adapter)
- **Apache Airflow** – orchestration (SQLite metadata)
- **Metabase** – BI (H2 metadata; connect to Dremio for data)

## Quick start

1. **Copy env and start services**

   ```bash
   cp .env.example .env
   # Required for lakehouse DAG: set absolute path to ./dbt
   echo "DBT_PROJECT_HOST_PATH=$(pwd)/dbt" >> .env
   docker compose up -d
   ```

2. **Wait for Airflow** (first run can take 1–2 minutes for init and image build).

   **Optional – Postgres for Airflow metadata:** `docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d`.

   **Terraform / cloud:** See **`docs/DEPLOYMENT.md`** and `terraform/README.md`.

3. **Open UIs**

   | Service   | URL              | Default login   |
   |----------|------------------|------------------|
   | Airflow  | http://localhost:8080 | admin / admin   |
   | Dremio   | http://localhost:9047  | set up on first visit |
   | MinIO    | http://localhost:9001 | dbt / minioadmin |
   | Metabase | http://localhost:3000 | set up on first visit |

4. **Test DAGs** (optional)  
   From the project root: `./scripts/airflow/test_dag.sh` (stack must be up). Or `pytest tests/ -v` if deps installed.

5. **Trigger pipeline**  
   In Airflow, enable and trigger **data_pipeline_lakehouse** (runs dbt against Dremio in a separate container via DockerOperator). Ensure raw Iceberg tables exist in MinIO and are visible in Dremio (see `docs/LAKEHOUSE.md`). If the DAG fails with mount errors, set `DBT_PROJECT_HOST_PATH` in `.env` to the absolute path of your `./dbt` folder.

6. **Connect Metabase to Dremio**  
   In Metabase: **Admin → Databases → Add database** → choose **Dremio**.  
   - **Host:** `dremio` | **Port:** `31010` | **Username/Password:** Dremio admin (created at http://localhost:9047).  
   See **`docs/METABASE_DREMIO.md`** if the connection fails.

## Project layout

See **`docs/PROJECT_STRUCTURE.md`** for the full structure. Summary:

```
├── .github/workflows/       # CI (dbt, DAG check, YAML) and CD (deploy)
├── airflow/
│   ├── CONNECTIONS.md       # Connections, troubleshooting
│   └── dags/                # mysql_to_landing, data_pipeline_lakehouse, test_connections + helpers
├── dbt/
│   ├── dbt_project.yml, profiles.yml, packages.yml
│   └── models/              # sources, schema, bronze/ stg/ silver/ gold/
├── docs/
│   └── PROJECT_STRUCTURE.md # Canonical project layout
├── scripts/
│   ├── infra/               # init-dbs.sh (when using docker-compose.postgres.yml)
│   └── airflow/             # test_dag.sh, test_connections.py
├── terraform/               # IaC: deploy on Docker, AWS, GCP, or Azure (see docs/DEPLOYMENT.md)
├── tests/                   # Pytest
├── docker-compose.yml       # MinIO, Dremio, Airflow, MySQL, Metabase
├── docker-compose.dev.yml / .staging.yml / .prod.yml
├── Dockerfile.airflow
└── README.md
```

## dbt (landing → bronze → silver → gold)

- **Layers**: **landing** (Parquet in MinIO) → **bronze** (stg_plants, stg_licenses) → **silver** (dw_dim_plant_profile, dw_dim_date) → **gold** (dm_plant).
- **Profile**: `data_tools`; target **dremio_dev** (Dremio).
- **Run dbt** (lakehouse): `./scripts/dbt/run_lakehouse.sh` or in Airflow trigger **data_pipeline_lakehouse**.
- **Local CLI**: `pip install -r dbt/requirements-dbt.txt`, then `dbt run` (set `DREMIO_HOST`, `DREMIO_PASSWORD` in env).
- **Structure**: See `dbt/README.md` and `dbt/models/README.md`.
- **Tests**: `dbt test`. Schema tests in `models/{bronze,silver,gold}/schema.yml`.

## Airflow

- **Executor**: LocalExecutor. **Metadata**: SQLite (no Postgres). dbt project mounted at `/opt/airflow/dbt`.
- **Default pipeline**: **data_pipeline_lakehouse** (dbt against Dremio). Trigger **test_connections** to verify MySQL and Dremio.
- Add **mysql_source** via `./scripts/airflow/add_connections.sh` (requires `MYSQL_PASSWORD`) or Admin → Connections. See `airflow/CONNECTIONS.md`.

### Ingestion (raw data)

- **MySQL → Landing (Parquet)**: Use **mysql_to_landing** DAG to sync MySQL → MinIO `landing` bucket as Parquet. Output: `s3://landing/mimdbuat01/{plants|licenses}/data.parquet`.
- **Add `mysql_source` before first run**:
  ```bash
  MYSQL_PASSWORD='your-password' ./scripts/airflow/add_connections.sh
  ```
  Or add manually in Airflow → Admin → Connections. See `airflow/CONNECTIONS.md`.
- **Lakehouse**: From landing Parquet, promote to Iceberg for Dremio (see **`docs/LAKEHOUSE.md`**). Or use Spark/Dremio/Airbyte for MySQL → Iceberg.
## Metabase

- Uses **H2** for its app database. Add **Dremio** as a data source in Metabase to query Iceberg tables.

## CI/CD

### CI (`.github/workflows/ci.yml`)

Runs on every **push** and **pull request** to `main` and `develop`:

- **dbt**: Runs `dbt deps` and `dbt compile` (no warehouse required).
- **Airflow DAGs**: Installs Airflow and validates that all DAGs in `airflow/dags/` load without import errors.
- **YAML**: Validates `dbt_project.yml`, `profiles.yml`, and model YAML files.

No secrets required for CI.

### CD (`.github/workflows/deploy.yml`)

Deploys the stack to **dev**, **staging**, or **prod**:

- **Trigger**: Push to `main` → deploys to **dev**. Use **Actions → Deploy → Run workflow** to pick **staging** or **prod**.
- **Method**: SSH into the target server, pull latest `main`, then run `docker compose up -d` (with optional env override: `docker-compose.dev.yml`, `docker-compose.staging.yml`, `docker-compose.prod.yml`).

**Setup:**

1. **Create GitHub Environments** (optional but recommended): Repo → Settings → Environments → add `dev`, `staging`, `prod`. You can add protection rules (e.g. require approval for `prod`).
2. **Secrets per environment**: In each environment (or in repo secrets), set:
   - `SSH_HOST` – hostname or IP of the deploy server
   - `SSH_USER` – SSH user (e.g. `deploy`)
   - `SSH_PRIVATE_KEY` – private key for that user (no passphrase, or use an agent)
   - `SSH_PORT` – (optional) default `22`
   - `DEPLOY_PATH` – (optional) path to repo on server, default `/opt/data-tools`
3. **On the server** (once):
   - Install Docker and Docker Compose.
   - Clone the repo: `git clone <your-repo-url> /opt/data-tools && cd /opt/data-tools`.
   - Create `.env` (copy from `.env.example`) and set strong passwords for that environment. Do not commit `.env`.
   - Ensure the SSH user can run `docker compose` (e.g. add user to `docker` group).

After each deploy, the workflow runs `git fetch && git reset --hard origin/main` in `DEPLOY_PATH`, then `docker compose -f docker-compose.yml -f docker-compose.<env>.yml up -d`.

## Optional: production

- Set strong `AIRFLOW_PASSWORD` and `DREMIO_PASSWORD` (and `MINIO_ROOT_PASSWORD`) in `.env`.
- For production Airflow metadata, use **docker-compose.postgres.yml** so Airflow uses Postgres instead of SQLite.
- Use Airflow Variables or secrets for Dremio credentials in **data_pipeline_lakehouse** if needed.
