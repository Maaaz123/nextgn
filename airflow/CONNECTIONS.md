# Airflow connections

**Default stack:** MinIO + Dremio + Iceberg. Airflow metadata = SQLite. No Postgres required.

---

## Secrets and credentials (source credentials in secret storage only)

**All usernames, passwords, API tokens, and any sensitive data for sources must be stored in secret storage only.** Do not put real credentials in code or in the repo.

| Source | Where to store secrets |
|--------|------------------------|
| **MySQL** | Airflow Connection `mysql_source` (or your conn id): set **Login** and **Password** in Admin → Connections. |
| **PostgreSQL** | Airflow Connection `postgres_source`: set **Login** and **Password** in Admin → Connections. |
| **SQL Server** | Airflow Connection `sqlserver_source`: set **Login** and **Password** in Admin → Connections. |
| **Oracle** | Airflow Connection `oracle_source`: set **Login** and **Password** in Admin → Connections. |
| **SAP HANA** | Airflow Connection `sap_hana_source`: set **Login** and **Password** in Admin → Connections (use Generic connection type; port 30015). |
| **Dremio** | Airflow Variable **`dremio_password`** (mark as *Sensitive* in UI). Optionally `dremio_user`. |
| **MinIO (landing)** | Airflow Variables **`minio_access_key`**, **`minio_secret_key`** (mark as *Sensitive*). Optionally **`minio_endpoint`**. |
| **API auth** | Airflow Variable per endpoint, e.g. **`api_example_com_token`** (mark as *Sensitive*). Reference in endpoint config as **`auth_variable`: `"api_example_com_token"`** — never put the token in the JSON. |

- Use **Admin → Connections** for DB sources: store host, schema, login, **password** in the connection (Airflow encrypts connection passwords).
- Use **Admin → Variables** for Dremio, MinIO, and API tokens; **mark variables as Sensitive** so they are masked in the UI and logs.
- For production, consider an external secrets backend (e.g. AWS Secrets Manager, HashiCorp Vault) and configure Airflow to use it for Connections/Variables.
- Local dev: you can use `.env` for convenience (e.g. `MYSQL_PASSWORD`, `DREMIO_PASSWORD`); **do not commit `.env`** and do not use real production credentials in it.

---

- **DAGs:** `airflow/dags/`
  - **test_connections** – test MySQL and Dremio
  - **mysql_to_landing** – MySQL → MinIO landing as Parquet
  - **postgres_to_landing** – PostgreSQL → MinIO landing as Parquet
  - **sqlserver_to_landing** – SQL Server → MinIO landing as Parquet
  - **oracle_to_landing** – Oracle → MinIO landing as Parquet
  - **sap_hana_to_landing** – SAP HANA → MinIO landing as Parquet
  - **api_to_landing** – HTTP API → MinIO landing as JSON or Parquet
  - **data_pipeline_lakehouse** – dbt against Dremio (default pipeline)
- **Config (tables/schemas/endpoints):** `airflow/dags/config/*.json` — see below.
- **Lakehouse setup:** `docs/LAKEHOUSE.md`

Set connections in **Airflow UI → Admin → Connections**.

**Test connections:** Trigger the **test_connections** DAG (tasks: test_mysql, test_dremio). From host: `python scripts/airflow/test_connections.py` (set `MYSQL_PASSWORD`).

---

## Table and endpoint config (JSON files)

Tables, schemas, and API endpoints can be defined in **JSON files** under `airflow/dags/config/` so you can version-control and edit them in your IDE. Each DAG loads its config from the file first; if the file is missing or invalid, it falls back to the Airflow Variable.

| File | Used by | Content |
|------|---------|--------|
| `mysql_to_landing_tables.json` | mysql_to_landing | List of `{ "conn_id?", "mysql_schema", "mysql_table", "primary_key" }` |
| `postgres_to_landing_tables.json` | postgres_to_landing | List of `{ "conn_id?", "schema", "table", "primary_key" }` |
| `sqlserver_to_landing_tables.json` | sqlserver_to_landing | List of `{ "conn_id?", "schema", "table", "primary_key" }` |
| `oracle_to_landing_tables.json` | oracle_to_landing | List of `{ "conn_id?", "schema", "table", "primary_key" }` |
| `sap_hana_to_landing_tables.json` | sap_hana_to_landing | List of `{ "conn_id?", "schema", "table", "primary_key" }` |
| `api_to_landing_endpoints.json` | api_to_landing | List of `{ "url", "key", "method?", "auth_variable?", "output_format?" }` |

- **Path:** `airflow/dags/config/<filename>`. The same directory is mounted with your DAGs in Docker, so editing the file in the repo updates the running config after the next DAG parse.
- **Format:** Each file is a JSON **array** of objects. You can also use a single object with a key `"tables"` or `"endpoints"` (e.g. `{"tables": [...]}`) and the loader will use that list.
- **Fallback:** If the file does not exist or is not valid JSON, the DAG uses the corresponding Airflow Variable (e.g. `mysql_to_landing_tables`). So you can keep using Variables if you prefer.

---

## Multiple databases (different IPs / hosts)

You can have **multiple MySQL, Postgres, or SQL Server instances** (different hosts/IPs) in the same DAG. For each source type:

1. Create **one Airflow Connection per instance** (e.g. `mysql_warehouse_a`, `mysql_warehouse_b` for two MySQL servers; `sqlserver_erp`, `sqlserver_crm` for two SQL Server boxes).
2. In the table-list Variable, each table entry can include optional **`conn_id`** to choose which connection to use. If omitted, the default connection (e.g. **mysql_conn_id** Variable) is used.

**Example – two SQL Servers at different IPs:**

- Connections: `sqlserver_erp` (host 10.0.0.1), `sqlserver_crm` (host 10.0.0.2).
- Variable **sqlserver_to_landing_tables**:
```json
[
  { "conn_id": "sqlserver_erp", "schema": "dbo", "table": "Orders", "primary_key": "id" },
  { "conn_id": "sqlserver_erp", "schema": "dbo", "table": "Products", "primary_key": "id" },
  { "conn_id": "sqlserver_crm", "schema": "dbo", "table": "Customers", "primary_key": "id" }
]
```

**Example – two MySQL servers:**

- Connections: `mysql_primary` (e.g. 192.168.1.10), `mysql_secondary` (192.168.1.11).
- Variable **mysql_to_landing_tables**:
```json
[
  { "conn_id": "mysql_primary", "mysql_schema": "mimdbuat01", "mysql_table": "plants", "primary_key": "id" },
  { "conn_id": "mysql_secondary", "mysql_schema": "appdb", "mysql_table": "events", "primary_key": "id" }
]
```

Same pattern for **postgres_to_landing_tables**, **oracle_to_landing_tables**, and **sap_hana_to_landing_tables**: add **`conn_id`** per entry when the table lives on a different connection/host.

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

Table list **mysql_to_landing_tables**: JSON array of `{ "mysql_schema", "mysql_table", "primary_key" }`. Optional **conn_id** per entry for multiple MySQL hosts (see "Multiple databases" above).

---

## PostgreSQL source (`postgres_source`)

Required for **postgres_to_landing** DAG.

| Field    | Value           |
|----------|-----------------|
| Conn Id  | `postgres_source` |
| Conn Type | **Postgres**   |
| Host     | *(your Postgres host)* |
| Schema   | *(e.g. `public`)* |
| Login    | *(your Postgres user)* |
| Password | *(set in UI)* |
| Port     | `5432`          |

Set **postgres_conn_id** Variable to your connection id if different (default: `postgres_source`). Table list **postgres_to_landing_tables**: JSON array of `{ "schema", "table", "primary_key" }`. Optional **conn_id** per entry for multiple Postgres hosts (see "Multiple databases" above).

---

## SQL Server source (`sqlserver_source`)

Required for **sqlserver_to_landing** DAG.

| Field    | Value           |
|----------|-----------------|
| Conn Id  | `sqlserver_source` |
| Conn Type | **Microsoft SQL Server** |
| Host     | *(your SQL Server host)* |
| Schema   | *(e.g. `dbo`)* |
| Login    | *(your SQL Server user)* |
| Password | *(set in UI)* |
| Port     | `1433`          |
| Extra   | *(optional)* `{"driver": "ODBC Driver 17 for SQL Server"}` |

Set **mssql_conn_id** Variable to your connection id if different (default: `sqlserver_source`). Table list **sqlserver_to_landing_tables**: JSON array of `{ "schema", "table", "primary_key" }`. Optional **conn_id** per entry for multiple SQL Server instances (different IPs; see "Multiple databases" above).

---

## Oracle source (`oracle_source`)

Required for **oracle_to_landing** DAG.

| Field    | Value           |
|----------|-----------------|
| Conn Id  | `oracle_source`  |
| Conn Type | **Oracle**    |
| Host     | *(your Oracle host)* |
| Schema   | *(e.g. your schema/owner)* |
| Login    | *(your Oracle user)* |
| Password | *(set in UI)* |
| Port     | `1521`          |
| Extra   | *(optional)* `{"service_name": "ORCL"}` or `{"sid": "ORCL"}` for DSN |

Set **oracle_conn_id** Variable to your connection id if different (default: `oracle_source`). Table list **oracle_to_landing_tables**: JSON array of `{ "schema", "table", "primary_key" }`. Optional **conn_id** per entry for multiple Oracle hosts. Use quoted identifiers in Oracle (case-sensitive); unquoted names are uppercased.

---

## SAP HANA source (`sap_hana_source`)

Required for **sap_hana_to_landing** DAG. Uses **Generic** (or custom) connection type; credentials from Connection, connect via **hdbcli**.

| Field    | Value           |
|----------|-----------------|
| Conn Id  | `sap_hana_source` |
| Conn Type | **Generic** (or any; host/login/password/port read by helper) |
| Host     | *(your SAP HANA host)* |
| Login    | *(your HANA user)* |
| Password | *(set in UI)* |
| Port     | `30015` (default HANA SQL port) |

Set **sap_hana_conn_id** Variable to your connection id if different (default: `sap_hana_source`). Table list **sap_hana_to_landing_tables**: JSON array of `{ "schema", "table", "primary_key" }`. Optional **conn_id** per entry for multiple SAP HANA hosts.

---

## API (HTTP) sources

**api_to_landing** DAG fetches from HTTP APIs and writes to the landing bucket. No Airflow connection is required; URLs and optional headers are configured via Variable **api_to_landing_endpoints** (JSON), e.g.:

```json
[
  { "url": "https://api.example.com/v1/data", "key": "api/example/data", "output_format": "parquet" },
  { "url": "https://api.example.com/events", "key": "api/events/data", "method": "GET", "output_format": "parquet" }
]
```

- **key**: S3 key in landing bucket; for Parquet (default) written as `{key}.parquet`.
- **method**: HTTP method (default `GET`).
- **auth_variable**: **(Recommended)** Airflow Variable name that holds the API token (e.g. `api_example_com_token`). Set the Variable in Admin → Variables and mark it *Sensitive*. Value can be `Bearer <token>` or just `<token>`. Do **not** put the token in the endpoint JSON.
- **headers**: Optional non-secret headers. For auth, use **auth_variable** instead of putting tokens in `headers`.
- **output_format**: `parquet` (default) – response must be JSON array of objects; write as Parquet. Use `json` only for non-tabular responses.

---

## Dremio

dbt runs against Dremio via **env vars** (no Airflow connection type). In Docker, Dremio is at `dremio:9047`.

**Best practice:** use **Airflow Variables** for credentials so they are not in code. The **data_pipeline_lakehouse** DAG reads these (with fallback to process env):

| Variable | Description | Example |
|----------|-------------|---------|
| `dremio_password` | Dremio user password (required in prod) | *(set in Admin → Variables)* |
| `dremio_user` | Dremio user | `admin` |
| `dremio_host` | Host for dbt container | `dremio` |
| `dremio_port` | Port | `9047` |
| `dremio_space` | dbt space in Dremio | `dbt` |

Set **dremio_password** in Admin → Variables (or ensure `DREMIO_PASSWORD` is in the environment that runs the scheduler/workers). For local dev you can set `DREMIO_PASSWORD` in `.env` and pass it to the DAG via the Docker env.

---

## DAG tags and parameterization

All DAGs are tagged by **environment** and **layer (spine/model)** so you can filter in the UI and run per env.

| Tag pattern | Meaning |
|-------------|---------|
| `env:dev` / `env:staging` / `env:prod` | From Variable `environment` (default `dev`) or `AIRFLOW_ENV` |
| `layer:ingestion` | Landing/ingestion DAG (mysql_to_landing) |
| `layer:transform` | Transform DAG (data_pipeline_lakehouse) |
| `layer:test` | Test DAG (test_connections) |
| `model:landing` / `model:lakehouse` / `model:connectivity` | Pipeline model type |
| `domain:plants` / `domain:licenses` / `domain:connectivity` | **Domain** – business domain (from tables or Variable `lakehouse_domains`) |

**Parameterized Variables (optional):**

| Variable | Used by | Default | Description |
|----------|---------|---------|-------------|
| `environment` | All DAGs (tags) | `dev` | env tag, e.g. `env:prod` |
| `lakehouse_domains` | data_pipeline_lakehouse (tags) | `plants,licenses` | Comma-separated domains for `domain:*` tags |
| `mysql_conn_id` | mysql_to_landing, test_connections | `mysql_source` | MySQL connection id |
| `postgres_conn_id` | postgres_to_landing | `postgres_source` | Postgres connection id |
| `mssql_conn_id` | sqlserver_to_landing | `sqlserver_source` | SQL Server connection id |
| `oracle_conn_id` | oracle_to_landing | `oracle_source` | Oracle connection id |
| `sap_hana_conn_id` | sap_hana_to_landing | `sap_hana_source` | SAP HANA connection id |
| `landing_bucket` | all landing DAGs | `landing` | MinIO bucket for Parquet/JSON |
| `mysql_to_landing_tables` | mysql_to_landing | *(built-in list)* | JSON array of `{mysql_schema, mysql_table, primary_key}`; optional **conn_id** per entry for multiple MySQL hosts |
| `postgres_to_landing_tables` | postgres_to_landing | *(built-in list)* | JSON array of `{schema, table, primary_key}`; optional **conn_id** per entry for multiple Postgres hosts |
| `sqlserver_to_landing_tables` | sqlserver_to_landing | *(built-in list)* | JSON array of `{schema, table, primary_key}`; optional **conn_id** per entry for multiple SQL Server instances (different IPs) |
| `oracle_to_landing_tables` | oracle_to_landing | *(built-in list)* | JSON array of `{schema, table, primary_key}`; optional **conn_id** per entry for multiple Oracle hosts |
| `sap_hana_to_landing_tables` | sap_hana_to_landing | *(built-in list)* | JSON array of `{schema, table, primary_key}`; optional **conn_id** per entry for multiple SAP HANA hosts |
| `api_to_landing_endpoints` | api_to_landing | *(built-in list)* | JSON array of `{url, key, method?, headers?, auth_variable?, output_format?}`; use **auth_variable** for API tokens (store token in that Variable, mark Sensitive) |
| `dbt_target` | data_pipeline_lakehouse | `dremio_dev` | dbt profile target (e.g. dremio_prod) |
| `dremio_host` / `dremio_port` | data_pipeline_lakehouse, test_connections | `dremio`, `9047` | Dremio host/port |
| `minio_endpoint` | landing_io (all landing DAGs) | *(env MINIO_ENDPOINT)* | MinIO endpoint URL (e.g. `http://minio:9000`) |
| `minio_access_key` | landing_io | *(env MINIO_ACCESS_KEY)* | MinIO access key — **store in Variable and mark Sensitive** in production |
| `minio_secret_key` | landing_io | *(env MINIO_SECRET_KEY)* | MinIO secret key — **store in Variable and mark Sensitive** in production |
