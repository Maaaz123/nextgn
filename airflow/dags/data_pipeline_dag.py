"""
DAG: Orchestrate full data pipeline – raw (ingestion) → bronze → stg → silver → gold.

1. Run mysql_to_postgres (load MySQL into Postgres raw layer).
2. When done, run dbt (deps, run, test) to build bronze → stg → silver → gold.

Trigger this DAG to run the entire pipeline; individual DAGs (mysql_to_postgres, dbt_transform)
can still be run separately.
"""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dag import TriggerDagRunOperator

# Same env as dbt_dag for warehouse connection
DBT_ENV = (
    "WAREHOUSE_HOST=postgres WAREHOUSE_PORT=5432 WAREHOUSE_USER=postgres "
    "WAREHOUSE_PASSWORD=postgres WAREHOUSE_DB=warehouse DBT_SCHEMA=public"
)

with DAG(
    dag_id="data_pipeline",
    default_args={
        "owner": "data",
        "retries": 1,
    },
    description="Orchestrate ingestion (MySQL→raw) then dbt (bronze→stg→silver→gold)",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["orchestration", "pipeline", "bronze", "silver", "gold"],
) as dag:
    # 1. Ingest: load MySQL into Postgres raw (trigger mysql_to_postgres and wait)
    ingest = TriggerDagRunOperator(
        task_id="ingest_mysql_to_raw",
        trigger_dag_id="mysql_to_postgres",
        wait_for_completion=True,
        poke_interval=60,
    )

    # 2. Transform: dbt bronze → stg → silver → gold (and tests)
    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd /opt/airflow/dbt && {DBT_ENV} dbt deps",
    )
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd /opt/airflow/dbt && {DBT_ENV} dbt run",
    )
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd /opt/airflow/dbt && {DBT_ENV} dbt test",
    )

    ingest >> dbt_deps >> dbt_run >> dbt_test
