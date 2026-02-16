"""
DAG: Lakehouse pipeline – MinIO + Apache Iceberg + Dremio + dbt.

1. Ingest: MySQL → Iceberg in MinIO (via Spark or Dremio; ensure raw Iceberg tables exist).
2. Transform: dbt run/test against Dremio in separate container.

Parameterized via Airflow Variables: environment, dbt_target, dremio_*.
"""
from datetime import datetime, timedelta
import os

from airflow import DAG
from airflow.models import Variable
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

# --- Parameterized config (Variables with fallbacks) ---
def _env():
    return Variable.get("environment", default_var=os.environ.get("AIRFLOW_ENV", "dev"))


def _dbt_target():
    return Variable.get("dbt_target", default_var=os.environ.get("DBT_TARGET", "dremio_dev"))


DBT_PROJECT_HOST_PATH = os.environ.get("DBT_PROJECT_HOST_PATH", "")
DBT_DOCKER_NETWORK = os.environ.get("DBT_DOCKER_NETWORK", "datatools_data_tools_network")


def _lakehouse_env():
    """Build env for dbt container; prefer Airflow Variables, fallback to os.environ."""
    return {
        "DREMIO_HOST": Variable.get("dremio_host", default_var=os.environ.get("DREMIO_HOST", "dremio")),
        "DREMIO_PORT": Variable.get("dremio_port", default_var=os.environ.get("DREMIO_PORT", "9047")),
        "DREMIO_USER": Variable.get("dremio_user", default_var=os.environ.get("DREMIO_USER", "admin")),
        "DREMIO_PASSWORD": Variable.get("dremio_password", default_var=os.environ.get("DREMIO_PASSWORD", "")),
        "DREMIO_OBJECT_STORAGE_SOURCE": Variable.get("dremio_object_storage_source", default_var="minio"),
        "DREMIO_OBJECT_STORAGE_PATH": Variable.get("dremio_object_storage_path", default_var="no_schema"),
        "DREMIO_SPACE": Variable.get("dremio_space", default_var="dbt"),
        "DREMIO_SPACE_FOLDER": Variable.get("dremio_space_folder", default_var="public"),
        "DBT_PROFILES_DIR": "/dbt",
    }


# Tags: environment + layer + domain (from Variable, comma-separated) + stack
def _lakehouse_domain_tags():
    raw = Variable.get("lakehouse_domains", default_var=os.environ.get("LAKEHOUSE_DOMAINS", "plants,licenses"))
    domains = [d.strip().lower() for d in raw.split(",") if d.strip()]
    return [f"domain:{d}" for d in domains]


_DAG_TAGS = [
    f"env:{_env()}",
    "layer:transform",
    "model:lakehouse",
] + _lakehouse_domain_tags() + ["lakehouse", "minio", "iceberg", "dremio", "dbt"]

with DAG(
    dag_id="data_pipeline_lakehouse",
    default_args={
        "owner": "data",
        "retries": 1,
        "retry_delay": timedelta(minutes=2),
    },
    description="Lakehouse: ingest to Iceberg (MinIO) then dbt against Dremio",
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=_DAG_TAGS,
) as dag:
    _target = _dbt_target()
    dbt_deps = DockerOperator(
        task_id="dbt_deps",
        image="data-tools-dbt",
        command=f"dbt deps --target {_target}",
        auto_remove=True,
        network_mode=DBT_DOCKER_NETWORK,
        environment=_lakehouse_env(),
        mount_tmp_dir=False,
        mounts=[Mount(source=DBT_PROJECT_HOST_PATH, target="/dbt", type="bind")]
        if DBT_PROJECT_HOST_PATH
        else [],
    )
    dbt_run = DockerOperator(
        task_id="dbt_run",
        image="data-tools-dbt",
        command=f"dbt run --target {_target}",
        auto_remove=True,
        network_mode=DBT_DOCKER_NETWORK,
        environment=_lakehouse_env(),
        mount_tmp_dir=False,
        mounts=[Mount(source=DBT_PROJECT_HOST_PATH, target="/dbt", type="bind")]
        if DBT_PROJECT_HOST_PATH
        else [],
    )
    dbt_test = DockerOperator(
        task_id="dbt_test",
        image="data-tools-dbt",
        command=f"dbt test --target {_target}",
        auto_remove=True,
        network_mode=DBT_DOCKER_NETWORK,
        environment=_lakehouse_env(),
        mount_tmp_dir=False,
        mounts=[Mount(source=DBT_PROJECT_HOST_PATH, target="/dbt", type="bind")]
        if DBT_PROJECT_HOST_PATH
        else [],
    )

    dbt_deps >> dbt_run >> dbt_test
