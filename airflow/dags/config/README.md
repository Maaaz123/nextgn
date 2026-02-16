# Landing config (tables & endpoints)

JSON files here define which **tables** (and optionally which **connection**) each ingestion DAG uses. The DAGs load from these files first; if a file is missing or invalid, they fall back to the Airflow Variable of the same name.

**Required keys** are validated at load time: missing keys raise a clear `ValueError` before any task runs.

- **mysql_to_landing_tables.json** – MySQL schema/table list (keys: `conn_id?`, `mysql_schema`, `mysql_table`, `primary_key`)
- **postgres_to_landing_tables.json** – Postgres schema/table list (`conn_id?`, `schema`, `table`, `primary_key`)
- **sqlserver_to_landing_tables.json** – SQL Server schema/table list (`conn_id?`, `schema`, `table`, `primary_key`)
- **oracle_to_landing_tables.json** – Oracle schema/table list (`conn_id?`, `schema`, `table`, `primary_key`)
- **sap_hana_to_landing_tables.json** – SAP HANA schema/table list (`conn_id?`, `schema`, `table`, `primary_key`)
- **api_to_landing_endpoints.json** – API endpoints (`url`, `key`, `method?`, `auth_variable?`, `output_format?`)

Use **conn_id** in a table entry to point that table to a different Airflow connection (e.g. another host). See `airflow/CONNECTIONS.md` for details.
