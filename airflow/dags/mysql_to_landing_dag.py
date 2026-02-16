"""MySQL → MinIO landing as Parquet. Config: dags/config/mysql_to_landing_tables.json or Variable."""
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from helpers.config_loader import load_json_config
from helpers.dag_utils import DEFAULT_ARGS, SCHEDULE, START_DATE, get_bucket, ingestion_tags
from helpers.mysql_to_landing import transfer_table_to_parquet

CONFIG_FILE = "mysql_to_landing_tables.json"
VARIABLE_NAME = "mysql_to_landing_tables"
DEFAULT_CONN = "mysql_source"
DEFAULT_TABLES = [
    {"mysql_schema": "mimdbuat01", "mysql_table": "plants", "primary_key": "id"},
    {"mysql_schema": "mimdbuat01", "mysql_table": "licenses", "primary_key": "id"},
    {"mysql_schema": "mimdbuat01", "mysql_table": "plant_products", "primary_key": "id"},
]

tables = load_json_config(
    CONFIG_FILE, VARIABLE_NAME, DEFAULT_TABLES,
    required_keys=["mysql_schema", "mysql_table"],
)
default_conn = Variable.get("mysql_conn_id", default_var=DEFAULT_CONN)


def _run_mysql(conn_id: str, schema: str, table: str, primary_key: str, **context):
    return transfer_table_to_parquet(
        mysql_conn_id=conn_id,
        mysql_schema=schema,
        mysql_table=table,
        landing_bucket=get_bucket(),
        primary_key=primary_key,
        logger=context["ti"].log,
    )


with DAG(
    dag_id="mysql_to_landing",
    default_args=DEFAULT_ARGS,
    description="MySQL → MinIO landing as Parquet",
    schedule=SCHEDULE,
    start_date=START_DATE,
    catchup=False,
    tags=ingestion_tags("mysql", tables, table_key="mysql_table", extra=["mysql"]),
) as dag:
    with TaskGroup("sync_tables"):
        for idx, cfg in enumerate(tables):
            conn_id = cfg.get("conn_id") or default_conn
            PythonOperator(
                task_id=f"{conn_id}_{cfg['mysql_schema']}_{cfg['mysql_table']}_{idx}",
                python_callable=_run_mysql,
                op_kwargs={
                    "conn_id": conn_id,
                    "schema": cfg["mysql_schema"],
                    "table": cfg["mysql_table"],
                    "primary_key": cfg.get("primary_key", "id") or None,
                },
                dag=dag,
            )