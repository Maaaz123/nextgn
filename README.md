# Data Tools Stack

Modern data stack for transformations, orchestration, and reporting:

- **PostgreSQL** – warehouse database (plus Airflow and Metabase metadata)
- **dbt Core** – SQL transformations (staging → marts)
- **Apache Airflow** – orchestration (scheduled dbt runs)
- **Metabase** – BI and reporting

## Quick start

1. **Copy env and start services**

   ```bash
   cp .env.example .env
   docker compose up -d
   ```

2. **Wait for Airflow** (first run can take 1–2 minutes for DB init and image build).

   **Alternative – Terraform / cloud:** Deploy the same stack with Terraform (local Docker, AWS, GCP, or Azure). Run `./scripts/deploy.sh terraform` or `./scripts/deploy.sh aws` (etc.). See **`docs/DEPLOYMENT.md`** and `terraform/README.md`.

3. **Open UIs**

   | Service   | URL              | Default login   |
   |----------|------------------|------------------|
   | Airflow  | http://localhost:8080 | admin / admin   |
   | Metabase | http://localhost:3000 | set up on first visit |
   | Postgres | localhost:5432   | postgres / postgres |

4. **Test DAGs before running** (optional but recommended)  
   From the project root:
   ```bash
   ./scripts/airflow/test_dag.sh
   ```
   This checks that DAGs load without import errors. Requires the stack to be up (`docker compose up -d`). If you have pytest and Airflow deps installed locally, you can also run: `pytest tests/ -v`.

5. **Trigger dbt**  
   In Airflow, enable and trigger the `dbt_transform` DAG (runs `dbt deps`, `dbt run`, `dbt test`).

6. **Connect Metabase to the warehouse**  
   In Metabase: **Admin → Databases → Add database**  
   - Host: `postgres` (from inside Docker) or `host.docker.internal` (from host)  
   - Port: `5432`  
   - Database: `warehouse`  
   - User / Password: same as in `.env` (e.g. postgres / postgres)  
   Use schemas `staging`, `marts`, and `raw` for reporting.

## Project layout

See **`docs/PROJECT_STRUCTURE.md`** for the full structure. Summary:

```
├── .github/workflows/       # CI (dbt, DAG check, YAML) and CD (deploy)
├── airflow/
│   ├── CONNECTIONS.md       # Connections, variables, troubleshooting
│   └── dags/                # data_pipeline, mysql_to_postgres, dbt_transform, test_connections + helpers
├── dbt/
│   ├── dbt_project.yml, profiles.yml, packages.yml
│   └── models/              # sources, schema, bronze/ stg/ silver/ gold/
├── docs/
│   └── PROJECT_STRUCTURE.md # Canonical project layout
├── scripts/
│   ├── infra/               # init-dbs.sh (Postgres DBs + raw schema)
│   ├── airflow/             # test_dag.sh, test_connections.py, generate_mysql_postgres_variable.py
│   └── db/                  # verify_postgres_raw.sh
├── terraform/               # IaC: deploy on Docker, AWS, GCP, or Azure (see docs/DEPLOYMENT.md)
├── tests/                   # Pytest (e.g. test_mysql_to_postgres.py)
├── docker-compose.yml       # Postgres, Airflow, Metabase (+ optional MySQL)
├── docker-compose.dev.yml / .staging.yml / .prod.yml
├── Dockerfile.airflow
└── README.md
```

## dbt (dl → stg → dw → dm)

- **Layers**: **raw** (Airflow) → **dl** (bronze / data lake views) → **stg** (transformation views) → **dw** (silver / data warehouse) → **dm** (gold / business marts).
- **Prefixes**: `dl_*` bronze, `stg_*` transformations, `dw_*` data warehouse, `dm_*` business.
- **Profile**: `data_tools`; target is driven by `WAREHOUSE_*` and `DBT_SCHEMA` env vars.
- **Run dbt without installing the CLI** (stack must be up): from project root run  
  `./scripts/dbt/run.sh test` or `./scripts/dbt/run.sh run` (uses the Airflow container).  
  If `dbt debug` reports "1 check failed" for git, you can ignore it: the DB connection is still OK and `dbt run` / `dbt test` work. We set `AIRFLOW__CORE__ENABLE_IMPLICIT_ALLOW=true` in Docker Compose to allow git; rebuild with `docker compose build airflow-webserver airflow-scheduler` and restart if you want the check to pass.
- **Run dbt with the CLI locally** – use **Python 3.8–3.12** (Python 3.14 is not yet supported by dbt and will cause import errors). Create a venv with a supported version, then install and run:

  ```bash
  cd dbt
  python3.11 -m venv .venv && source .venv/bin/activate   # or python3.12
  pip install -r requirements-dbt.txt
  export WAREHOUSE_HOST=localhost WAREHOUSE_USER=postgres WAREHOUSE_PASSWORD=postgres WAREHOUSE_DB=warehouse
  dbt deps && dbt run && dbt test
  ```

  If you use [pyenv](https://github.com/pyenv/pyenv), the repo has a `.python-version` (3.11) so `pyenv install` then `cd dbt` will use the right version.

  **If `python3.11` is not found on macOS:** install it with Homebrew: `brew install python@3.11`, then create the venv with the full path:  
  `$(brew --prefix python@3.11)/bin/python3.11 -m venv .venv && source .venv/bin/activate`.  
  Or try `python3.12` (install with `brew install python@3.12` if needed).

- Sources: `raw.flows`, `raw.plants`, `raw.licenses` (from mysql_to_postgres). Add more in `models/sources.yml` and corresponding bronze/silver/gold models.
- **Tests & data quality**: Schema tests in `models/schema.yml` (unique, not_null on keys); source column tests in `models/sources.yml`; singular DQ tests in `dbt/tests/` (no future dates, no negative counts, referential fact→dim). Run: `dbt test`. The **dbt_transform** DAG already runs `dbt test` after `dbt run`.

## Airflow

- **Executor**: LocalExecutor (no extra Redis/Celery).
- dbt project is mounted at `/opt/airflow/dbt`; the `dbt_transform` DAG runs in that directory with env vars pointing at the `warehouse` database.
- To change schedule or add ingestion DAGs, add or edit Python files in `airflow/dags/`.

### MySQL → Postgres (data move)

The **mysql_to_postgres** DAG syncs tables from MySQL into the Postgres warehouse (schema `raw` by default).

1. **Add Airflow connections** (Admin → Connections):
   - **Connection Id**: `mysql_source`  
     **Type**: MySQL  
     **Host**: your MySQL host (e.g. `mysql` if using the optional MySQL container, or your server IP)  
     **Schema**: MySQL database name  
     **Login / Password**: MySQL user and password  
     **Port**: 3306  
   - **Connection Id**: `postgres_warehouse`  
     **Type**: Postgres  
     **Host**: `postgres`  
     **Schema**: `warehouse`  
     **Login / Password**: same as `POSTGRES_USER` / `POSTGRES_PASSWORD` from `.env`  
     **Port**: 5432  

2. **Choose tables to sync**  
   - **Option A**: Edit the default in `airflow/dags/mysql_to_postgres_dag.py` (list `DEFAULT_TABLES`).  
   - **Option B**: In Airflow, Admin → Variables → Add:  
     **Key**: `mysql_to_postgres_tables`  
     **Val** (JSON):  
     `[{"mysql_schema": "mydb", "mysql_table": "users", "postgres_schema": "raw", "postgres_table": "users"}]`  
     Add one object per table; `postgres_schema`/`postgres_table` default to `raw` and the source table name.

3. **Optional: run MySQL in Docker**  
   The compose file includes an optional `mysql` service. If you use it, set the `mysql_source` connection host to `mysql`, schema to `MYSQL_DATABASE` (e.g. `mydb`), and login/password to `MYSQL_USER`/`MYSQL_PASSWORD`. Create a test table (e.g. `users`) in that database, then trigger the DAG.

4. **Run the DAG**  
   Enable and trigger **mysql_to_postgres** in the Airflow UI. It runs hourly; data is full-refresh (truncate + insert) into Postgres. Synced tables appear in the `raw` schema for dbt or Metabase.

## Metabase

- Uses the same Postgres instance; its metadata is stored in the `metabase` database.
- Add the **warehouse** database in Metabase for dashboards and reports on `raw`, `staging`, and `marts`.

## CI/CD

### CI (`.github/workflows/ci.yml`)

Runs on every **push** and **pull request** to `main` and `develop`:

- **dbt**: Starts a Postgres service, creates `raw.example_events`, runs `dbt deps`, `dbt compile`, `dbt run`, `dbt test`.
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

- Set strong `POSTGRES_PASSWORD` and `AIRFLOW_PASSWORD` in `.env`.
- Use Airflow Variables or secrets for `WAREHOUSE_PASSWORD` in the dbt DAG instead of hardcoding.
- Consider separate Postgres instances for Airflow metadata and warehouse.
- Run Metabase with a dedicated Postgres for its app DB if you scale.
