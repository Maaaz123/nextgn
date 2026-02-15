"""
DAG: MySQL → MinIO landing bucket as Parquet.

- Connection: mysql_source (Admin → Connections)
- Env/Variables: MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, LANDING_BUCKET
- Output: s3://landing/{schema}/{table}/data.parquet
"""
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

from helpers.mysql_to_landing import transfer_table_to_parquet

MYSQL_CONN_ID = "mysql_source"
LANDING_BUCKET = "landing"

DEFAULT_TABLES = [
    {"mysql_schema": "mimdbuat01", "mysql_table": "plants", "primary_key": "id"},
    {"mysql_schema": "mimdbuat01", "mysql_table": "licenses", "primary_key": "id"},
]


def _make_task(mysql_schema: str, mysql_table: str, primary_key: str = "id"):
    def _run(**context):
        ti = context["ti"]
        return transfer_table_to_parquet(
            mysql_conn_id=MYSQL_CONN_ID,
            mysql_schema=mysql_schema,
            mysql_table=mysql_table,
            landing_bucket=LANDING_BUCKET,
            primary_key=primary_key,
            logger=ti.log,
        )

    return _run


with DAG(
    dag_id="mysql_to_landing",
    default_args={"owner": "data", "retries": 1},
    description="MySQL → MinIO landing as Parquet (plants, licenses)",
    schedule_interval="@hourly",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["mysql", "minio", "parquet", "landing", "ingestion"],
) as dag:
    with TaskGroup(group_id="sync_tables") as sync_tasks:
        for idx, cfg in enumerate(DEFAULT_TABLES):
            PythonOperator(
                task_id=f"{cfg['mysql_schema']}_{cfg['mysql_table']}_{idx}",
                python_callable=_make_task(
                    mysql_schema=cfg["mysql_schema"],
                    mysql_table=cfg["mysql_table"],
                    primary_key=cfg.get("primary_key", "id"),
                ),
                dag=dag,
            )
