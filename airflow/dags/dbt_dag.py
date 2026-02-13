"""
DAG: Run dbt Core (run + test) on a schedule.
Uses BashOperator; dbt and project are available in the Airflow image and volume.
"""
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

# Connection to warehouse: same Postgres host, database 'warehouse'
# Set these in Docker Compose or Airflow Variables for the worker/scheduler
ENV = "WAREHOUSE_HOST=postgres WAREHOUSE_PORT=5432 WAREHOUSE_USER=postgres WAREHOUSE_PASSWORD=postgres WAREHOUSE_DB=warehouse DBT_SCHEMA=public"

with DAG(
    dag_id="dbt_transform",
    default_args={
        "owner": "data",
        "retries": 1,
    },
    description="Run dbt models and tests against the warehouse",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["dbt", "transform"],
) as dag:
    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd /opt/airflow/dbt && {ENV} dbt deps",
    )
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd /opt/airflow/dbt && {ENV} dbt run",
    )
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd /opt/airflow/dbt && {ENV} dbt test",
    )
    dbt_deps >> dbt_run >> dbt_test
