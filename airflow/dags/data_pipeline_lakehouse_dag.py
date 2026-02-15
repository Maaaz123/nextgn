"""
DAG: Lakehouse pipeline – MinIO + Apache Iceberg + Dremio + dbt.

1. Ingest: MySQL → Iceberg in MinIO (via Spark or Dremio; ensure raw Iceberg tables exist).
2. Transform: dbt run/test against Dremio (--target dremio_dev) in separate container.

dbt runs in DockerOperator (standalone dbt image) to avoid protobuf conflict with Airflow.
Set DBT_PROJECT_HOST_PATH in .env to the absolute path of your ./dbt folder.
"""
from datetime import datetime
import os

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

# Host path to dbt project (required for DockerOperator bind mount)
DBT_PROJECT_HOST_PATH = os.environ.get("DBT_PROJECT_HOST_PATH", "")
# Network name: docker compose creates {project}_{network}. Default: datatools_data_tools_network
DBT_DOCKER_NETWORK = os.environ.get("DBT_DOCKER_NETWORK", "datatools_data_tools_network")

LAKEHOUSE_ENV = {
    "DREMIO_HOST": "dremio",
    "DREMIO_PORT": "9047",
    "DREMIO_USER": "admin",
    "DREMIO_PASSWORD": "Maaz123123123@f",
    "DREMIO_OBJECT_STORAGE_SOURCE": "minio",
    "DREMIO_OBJECT_STORAGE_PATH": "no_schema",
    "DREMIO_SPACE": "dbt",
    "DREMIO_SPACE_FOLDER": "public",
    "DBT_PROFILES_DIR": "/dbt",
}

with DAG(
    dag_id="data_pipeline_lakehouse",
    default_args={
        "owner": "data",
        "retries": 1,
    },
    description="Lakehouse: ingest to Iceberg (MinIO) then dbt against Dremio",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["lakehouse", "minio", "iceberg", "dremio", "dbt"],
) as dag:
    dbt_deps = DockerOperator(
        task_id="dbt_deps",
        image="data-tools-dbt",
        command="dbt deps --target dremio_dev",
        auto_remove=True,
        network_mode=DBT_DOCKER_NETWORK,
        environment=LAKEHOUSE_ENV,
        mount_tmp_dir=False,
        mounts=[Mount(source=DBT_PROJECT_HOST_PATH, target="/dbt", type="bind")]
        if DBT_PROJECT_HOST_PATH
        else [],
    )
    dbt_run = DockerOperator(
        task_id="dbt_run",
        image="data-tools-dbt",
        command="dbt run --target dremio_dev",
        auto_remove=True,
        network_mode=DBT_DOCKER_NETWORK,
        environment=LAKEHOUSE_ENV,
        mount_tmp_dir=False,
        mounts=[Mount(source=DBT_PROJECT_HOST_PATH, target="/dbt", type="bind")]
        if DBT_PROJECT_HOST_PATH
        else [],
    )
    dbt_test = DockerOperator(
        task_id="dbt_test",
        image="data-tools-dbt",
        command="dbt test --target dremio_dev",
        auto_remove=True,
        network_mode=DBT_DOCKER_NETWORK,
        environment=LAKEHOUSE_ENV,
        mount_tmp_dir=False,
        mounts=[Mount(source=DBT_PROJECT_HOST_PATH, target="/dbt", type="bind")]
        if DBT_PROJECT_HOST_PATH
        else [],
    )

    dbt_deps >> dbt_run >> dbt_test
