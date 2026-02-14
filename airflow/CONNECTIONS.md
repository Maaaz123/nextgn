# Airflow connections for MySQL → Postgres

**Where is the Airflow code?**

- **DAGs:** `airflow/dags/`  
  - `mysql_to_postgres_dag.py` – MySQL → Postgres sync DAG  
  - `dbt_dag.py` – dbt run/test DAG  
  - `data_pipeline_dag.py` – **full pipeline**: ingest (MySQL→raw) then dbt (bronze→stg→silver→gold)  
- **Transfer logic:** `airflow/dags/helpers/mysql_to_postgres.py`  
- **Connection guide:** this file (`airflow/CONNECTIONS.md`)

Set connections in **Airflow UI → Admin → Connections**. Do not commit passwords to the repo.

**Test connections:** Trigger the **test_connections** DAG in Airflow (it runs two tasks: test_mysql, test_postgres). Or from the project root run: `python scripts/airflow/test_connections.py` (set `MYSQL_PASSWORD` and optionally `POSTGRES_*` in env or `.env`).

---

## 1. MySQL source (`mysql_source`)

| Field    | Value           |
|----------|-----------------|
| Conn Id  | `mysql_source`  |
| Conn Type | **MySQL**    |
| Host     | `34.166.142.13` |
| Schema   | `mimdbuat01`    |
| Login    | `mimdbuat01-user` |
| Password | *(set in UI – use your MySQL password)* |
| Port     | `3306`          |

---

## 2. Postgres destination (`postgres_warehouse`)

**Important:** The **Schema** field is the **database name** in Postgres. To have tables and data in the **postgres** database, you must set **Schema** = `postgres`. Data is written into the **raw** schema inside that database (so you get `postgres.raw.flows`, `postgres.raw.plants`, `postgres.raw.licenses`). If Schema is wrong, you will see no tables in the database you’re looking at.

Use **Host** = `postgres` when Airflow runs in Docker (same compose). Use `localhost` only if Airflow runs on the host.

| Field    | Value              |
|----------|--------------------|
| Conn Id  | `postgres_warehouse` |
| Conn Type | **Postgres**     |
| Host     | `postgres` *(or `localhost` if Airflow is not in Docker)* |
| **Schema** | **`postgres`** *(must be exactly `postgres` to write to postgres DB; this is the database name)* |
| Login    | `postgres`        |
| Password | `postgres` *(or set in UI)* |
| Port     | `5432`            |

After the DAG runs, verify: connect to database **postgres** and run `SELECT * FROM raw.flows LIMIT 5;` or use `./scripts/db/verify_postgres_raw.sh` from the project root.

**Full pipeline (data_pipeline DAG):** For end-to-end runs (ingest → dbt), set **Schema** to the same database dbt uses. The pipeline DAG uses `WAREHOUSE_DB=warehouse`; if you use that, set **Schema** = `warehouse` so raw and dbt models live in one database. If you use `postgres` for everything, set Schema = `postgres` and change `WAREHOUSE_DB` in `data_pipeline_dag.py` (and `dbt_dag.py`) to `postgres`.

---

## 3. Tables to sync

The DAG defaults to syncing **flows**, **plants**, and **licenses** from `mimdbuat01` → `raw` using **incremental load** (only new or updated rows, by `updated_at`). You can add more tables in two ways.

**Incremental load:** For each table you can set `incremental_column` (e.g. `updated_at`) and `primary_key` (e.g. `id`) in the table config. The first run does a full load; later runs only fetch rows where `incremental_column > last_value` and upsert into Postgres. State is stored in `raw._sync_state`. Omit `incremental_column` for full refresh (truncate + insert) only.

---

### Option A: Many tables, same schema (e.g. 100 tables)

Best when all tables are in the same MySQL database and go to the same Postgres schema.

1. In **Admin → Variables**, create:
   - **Key:** `mysql_to_postgres_table_list`  
   - **Val:** a JSON array of table names only, e.g.:
     ```json
     ["flows", "users", "orders", "products", "customers"]
     ```
   Add all 100 table names in that array.

2. Optional: set **`mysql_to_postgres_schema`** = `mimdbuat01` and **`mysql_to_postgres_postgres_schema`** = `raw` if you need different schemas (defaults are mimdbuat01 and raw).

3. The DAG will create **one task per table** (e.g. 100 tasks under the `sync_tables` group). They run in parallel. Enable and trigger the **mysql_to_postgres** DAG.

**Generate the list from a file:** if you have a file with one table name per line (`tables.txt`):
```bash
python scripts/airflow/generate_mysql_postgres_variable.py tables.txt --simple
```
Copy the output into Variable **`mysql_to_postgres_table_list`**.

---

### Option B: Full control (different schemas or table names per table)

In **Admin → Variables** set:

- **Key:** `mysql_to_postgres_tables`
- **Val:** (JSON array of objects)

Example – one table:

```json
[
  {"mysql_schema": "mimdbuat01", "mysql_table": "flows", "postgres_schema": "raw", "postgres_table": "flows"}
]
```

Example – multiple tables (same schema):

```json
[
  {"mysql_schema": "mimdbuat01", "mysql_table": "flows", "postgres_schema": "raw", "postgres_table": "flows"},
  {"mysql_schema": "mimdbuat01", "mysql_table": "users", "postgres_schema": "raw", "postgres_table": "users"}
]
```

To generate this JSON from a list of table names:
```bash
python scripts/airflow/generate_mysql_postgres_variable.py tables.txt
```
Copy the output into Variable **`mysql_to_postgres_tables`**.

Save, then enable and trigger the **mysql_to_postgres** DAG.

---

## Troubleshooting: no tables created, no data moved

Follow these steps in order:

| Step | Action | What to check |
|------|--------|---------------|
| 1 | **Test connections** | Airflow → trigger **test_connections** DAG. Both tasks must pass. If they fail, fix `mysql_source` and `postgres_warehouse` in Admin → Connections. |
| 2 | **Postgres Schema (database)** | Admin → Connections → `postgres_warehouse` → **Schema** must be the database name: `warehouse` or `postgres`. Data goes to `raw` schema inside that DB. |
| 3 | **Run verify script** | From project root: `./scripts/db/verify_postgres_raw.sh` – checks both `warehouse` and `postgres` databases. |
| 4 | **Check DAG run** | mysql_to_postgres → open latest run → did tasks succeed or fail? Click a task → **Log** to see errors. |
| 5 | **MySQL tables exist?** | On MySQL: `SELECT COUNT(*) FROM flows` (etc.). If empty or missing, fix source data first. |
| 6 | **MySQL reachable from Docker?** | If Airflow runs in Docker, MySQL at `34.166.142.13` must accept connections from your machine. Firewall/security group must allow port 3306. |

**Common fix:** Set `postgres_warehouse` **Schema** = `warehouse` (recommended; init-dbs creates raw there). Then trigger mysql_to_postgres again.

---

## Troubleshooting: no data in Postgres (detailed)

1. **Check task logs**  
   In Airflow UI → **mysql_to_postgres** DAG → open a run → click a task (e.g. `mimdbuat01_flows_0`) → **Log**. Look for Python errors or connection errors.

2. **Postgres connection – database (Schema)**  
   The **Schema** field in the `postgres_warehouse` connection is the **database name**. To load into the `postgres` database, set **Schema** = `postgres`. If you use the `warehouse` database from docker-compose, set **Schema** = `warehouse`. Data is written into the **raw** schema inside that database (e.g. `postgres.raw.flows` or `warehouse.raw.flows`). Check the correct database and schema in your SQL client.

3. **Postgres host when Airflow runs in Docker**  
   From inside the container, use **Host** = `postgres` (the service name), not `localhost`. Use `localhost` only if Airflow runs on the host machine.

4. **MySQL reachable from Airflow**  
   If Airflow runs in Docker, it must reach MySQL at `34.166.142.13`. Ensure the server allows connections from the machine running Docker (firewall / security group). Test from the host: `mysql -h 34.166.142.13 -u mimdbuat01-user -p mimdbuat01 -e "SELECT 1"`.

5. **Primary key / upsert errors**  
   If you see “there is no unique or exclusion constraint” in the logs, the code will try to add a primary key and, if that fails, will fall back to truncate + insert so data still loads. If the task still fails, drop the target table in Postgres and trigger the DAG again so the table is recreated with a primary key.

6. **Database is postgres but no tables / no data**  
   In Airflow go to **Admin → Connections → postgres_warehouse** and set **Schema** to exactly **postgres** (this is the database name). Save. Trigger **mysql_to_postgres** again. In the task log you should see: `Postgres target: host=postgres database(schema field)=postgres → tables in schema 'raw'`. If you see `database(schema field)=warehouse` or empty, fix Schema to `postgres` and re-run. After a successful run, from project root run: `./scripts/db/verify_postgres_raw.sh` to list tables and row counts in database postgres.
