"""
DAG: MySQL → PostgreSQL table sync.

- Connections: mysql_source, postgres_warehouse (set in Admin → Connections).
- Table list: Airflow Variable mysql_to_postgres_tables (JSON array), or default below.
"""
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

from helpers.mysql_to_postgres import get_tables_config, transfer_table

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

DAG_ID = "mysql_to_postgres"
MYSQL_CONN_ID = "mysql_source"
POSTGRES_CONN_ID = "postgres_warehouse"
VARIABLE_TABLES_KEY = "mysql_to_postgres_tables"

# incremental_column: sync only new/updated rows (by this column). primary_key: used for upsert.
DEFAULT_TABLES = [
    {
        "mysql_schema": "mimdbuat01",
        "mysql_table": "flows",
        "postgres_schema": "raw",
        "postgres_table": "flows",
        "incremental_column": "updated_at",
        "primary_key": "id",
    },
    {
        "mysql_schema": "mimdbuat01",
        "mysql_table": "plants",
        "postgres_schema": "raw",
        "postgres_table": "plants",
        "incremental_column": "updated_at",
        "primary_key": "id",
    },
    {
        "mysql_schema": "mimdbuat01",
        "mysql_table": "licenses",
        "postgres_schema": "raw",
        "postgres_table": "licenses",
        "incremental_column": "updated_at",
        "primary_key": "id",
    },
]


def _make_transfer_task(
    mysql_schema: str,
    mysql_table: str,
    postgres_schema: str,
    postgres_table: str,
    incremental_column: str | None = None,
    primary_key: str = "id",
):
    """Build a callable for PythonOperator that runs transfer_table with task logger."""

    def _run(**context):
        ti = context["ti"]
        logger = ti.log
        return transfer_table(
            mysql_conn_id=MYSQL_CONN_ID,
            postgres_conn_id=POSTGRES_CONN_ID,
            mysql_schema=mysql_schema,
            mysql_table=mysql_table,
            postgres_schema=postgres_schema,
            postgres_table=postgres_table,
            incremental_column=incremental_column,
            primary_key=primary_key,
            logger=logger,
        )

    return _run


# -----------------------------------------------------------------------------
# DAG definition
# ------------------------------------------------------------------------------

with DAG(
    dag_id=DAG_ID,
    default_args={
        "owner": "data",
        "retries": 1,
    },
    description="Sync tables from MySQL to PostgreSQL (incremental by updated_at or full refresh).",
    schedule_interval="@hourly",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["mysql", "postgres", "ingestion"],
) as dag:
    tables_config = get_tables_config(
        variable_key=VARIABLE_TABLES_KEY,
        default_tables=DEFAULT_TABLES,
    )

    with TaskGroup(group_id="sync_tables") as sync_tasks:
        for idx, cfg in enumerate(tables_config):
            mysql_schema = cfg["mysql_schema"]
            mysql_table = cfg["mysql_table"]
            postgres_schema = cfg.get("postgres_schema", "raw")
            postgres_table = cfg.get("postgres_table", mysql_table)
            incremental_column = cfg.get("incremental_column")
            primary_key = cfg.get("primary_key", "id")

            task_id = f"{mysql_schema}_{mysql_table}_{idx}"

            PythonOperator(
                task_id=task_id,
                python_callable=_make_transfer_task(
                    mysql_schema=mysql_schema,
                    mysql_table=mysql_table,
                    postgres_schema=postgres_schema,
                    postgres_table=postgres_table,
                    incremental_column=incremental_column,
                    primary_key=primary_key,
                ),
                dag=dag,
            )
