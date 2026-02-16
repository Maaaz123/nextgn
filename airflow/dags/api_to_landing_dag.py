"""API → MinIO landing as JSON or Parquet. Config: dags/config/api_to_landing_endpoints.json or Variable."""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

from helpers.api_to_landing import fetch_api_to_landing
from helpers.config_loader import load_json_config
from helpers.dag_utils import DEFAULT_ARGS, SCHEDULE, START_DATE, api_domain_tags, get_bucket, ingestion_tags

CONFIG_FILE = "api_to_landing_endpoints.json"
VARIABLE_NAME = "api_to_landing_endpoints"
DEFAULT_ENDPOINTS = [{"url": "https://api.example.com/data", "key": "api/example/data", "output_format": "parquet"}]

endpoints = load_json_config(
    CONFIG_FILE, VARIABLE_NAME, DEFAULT_ENDPOINTS,
    required_keys=["url", "key"],
)


def _run_api(url: str, key: str, method: str, headers: dict | None, auth_var: str | None, output_format: str, **context):
    return fetch_api_to_landing(
        url=url,
        landing_bucket=get_bucket(),
        key=key,
        method=method,
        headers=headers,
        auth_variable=auth_var,
        output_format=output_format,
        logger=context["ti"].log,
    )


with DAG(
    dag_id="api_to_landing",
    default_args=DEFAULT_ARGS,
    description="API → MinIO landing as JSON or Parquet",
    schedule=SCHEDULE,
    start_date=START_DATE,
    catchup=False,
    tags=ingestion_tags("api", [], extra=["api", "http"], domain_list=api_domain_tags(endpoints)),
) as dag:
    with TaskGroup("fetch_endpoints"):
        for idx, cfg in enumerate(endpoints):
            task_id = f"fetch_{idx}_{cfg['key'].replace('/', '_')[:50]}"
            PythonOperator(
                task_id=task_id,
                python_callable=_run_api,
                op_kwargs={
                    "url": cfg["url"],
                    "key": cfg["key"],
                    "method": cfg.get("method", "GET"),
                    "headers": cfg.get("headers"),
                    "auth_var": cfg.get("auth_variable"),
                    "output_format": cfg.get("output_format", "parquet"),
                },
                dag=dag,
            )