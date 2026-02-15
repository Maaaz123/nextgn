# Airflow connections

**Default stack:** MinIO + Dremio + Iceberg. Airflow metadata = SQLite. No Postgres required.

- **DAGs:** `airflow/dags/`
  - **test_connections** – test MySQL and Dremio
  - **mysql_to_landing** – MySQL → MinIO landing as Parquet (plants, licenses)
  - **data_pipeline_lakehouse** – dbt against Dremio (default pipeline)
- **Lakehouse setup:** `docs/LAKEHOUSE.md`

Set connections in **Airflow UI → Admin → Connections**.

**Test connections:** Trigger the **test_connections** DAG (tasks: test_mysql, test_dremio). From host: `python scripts/airflow/test_connections.py` (set `MYSQL_PASSWORD`).

---

## MySQL source (`mysql_source`)

Required for **mysql_to_landing** DAG.

| Field    | Value           |
|----------|-----------------|
| Conn Id  | `mysql_source`  |
| Conn Type | **MySQL**    |
| Host     | *(your MySQL host)* |
| Schema   | `mimdbuat01`    |
| Login    | *(your MySQL user)* |
| Password | *(set in UI)* |
| Port     | `3306`          |

**Add via script:** `MYSQL_PASSWORD='your-password' ./scripts/airflow/add_connections.sh`

---

## Dremio

dbt runs against Dremio via env vars (no Airflow connection needed). When Airflow runs in Docker, Dremio is reached at `dremio:9047`. Credentials are set in **data_pipeline_lakehouse** DAG or via Airflow Variables.
