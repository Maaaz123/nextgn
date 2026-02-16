"""SAP HANA → MinIO landing as Parquet. Config: dags/config/sap_hana_to_landing_tables.json or Variable."""
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

from helpers.config_loader import load_json_config
from helpers.dag_utils import DEFAULT_ARGS, SCHEDULE, START_DATE, get_bucket, ingestion_tags
from helpers.sap_hana_to_landing import transfer_table_to_parquet

CONFIG_FILE = "sap_hana_to_landing_tables.json"
VARIABLE_NAME = "sap_hana_to_landing_tables"
DEFAULT_CONN = "sap_hana_source"
DEFAULT_TABLES = [{"schema": "MYSCHEMA", "table": "EXAMPLE_TABLE", "primary_key": "id"}]

tables = load_json_config(
    CONFIG_FILE, VARIABLE_NAME, DEFAULT_TABLES,
    required_keys=["schema", "table"],
)
default_conn = Variable.get("sap_hana_conn_id", default_var=DEFAULT_CONN)


def _run_sap_hana(conn_id: str, schema: str, table: str, primary_key: str, **context):
    return transfer_table_to_parquet(
        sap_hana_conn_id=conn_id,
        schema=schema,
        table=table,
        landing_bucket=get_bucket(),
        primary_key=primary_key,
        logger=context["ti"].log,
    )


with DAG(
    dag_id="sap_hana_to_landing",
    default_args=DEFAULT_ARGS,
    description="SAP HANA → MinIO landing as Parquet",
    schedule=SCHEDULE,
    start_date=START_DATE,
    catchup=False,
    tags=ingestion_tags("sap_hana", tables, extra=["sap_hana", "hana"]),
) as dag:
    with TaskGroup("sync_tables"):
        for idx, cfg in enumerate(tables):
            conn_id = cfg.get("conn_id") or default_conn
            PythonOperator(
                task_id=f"{conn_id}_{cfg['schema']}_{cfg['table']}_{idx}",
                python_callable=_run_sap_hana,
                op_kwargs={
                    "conn_id": conn_id,
                    "schema": cfg["schema"],
                    "table": cfg["table"],
                    "primary_key": cfg.get("primary_key", "id"),
                },
                dag=dag,
            )
