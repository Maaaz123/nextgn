"""
DAG: Test MySQL and Postgres connections (mysql_source, postgres_warehouse).

Run this DAG to verify both connections work before running mysql_to_postgres.
Create connections in Admin → Connections first (see airflow/CONNECTIONS.md).
"""
import traceback
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.providers.postgres.hooks.postgres import PostgresHook

MYSQL_CONN_ID = "mysql_source"
POSTGRES_CONN_ID = "postgres_warehouse"


def test_mysql(**context):
    ti = context["ti"]
    ti.log.info("Testing connection: %s (create in Admin → Connections if missing)", MYSQL_CONN_ID)
    try:
        hook = MySqlHook(mysql_conn_id=MYSQL_CONN_ID, schema="mimdbuat01")
        conn = hook.get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            row = cur.fetchone()
        conn.close()
        c = hook.get_connection(MYSQL_CONN_ID)
        msg = f"MySQL OK: host={c.host} port={c.port} schema=mimdbuat01 result={row}"
        ti.log.info(msg)
        return msg
    except Exception as e:
        ti.log.error("MySQL connection failed: %s", e)
        ti.log.error(traceback.format_exc())
        raise


def test_postgres(**context):
    ti = context["ti"]
    ti.log.info("Testing connection: %s (create in Admin → Connections if missing)", POSTGRES_CONN_ID)
    try:
        hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        conn = hook.get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            row = cur.fetchone()
        conn.close()
        c = hook.get_connection(POSTGRES_CONN_ID)
        db = getattr(c, "schema", "") or "(schema field empty)"
        msg = f"Postgres OK: host={c.host} port={c.port} database={db} result={row}"
        ti.log.info(msg)
        return msg
    except Exception as e:
        ti.log.error("Postgres connection failed: %s", e)
        ti.log.error(traceback.format_exc())
        raise


with DAG(
    dag_id="test_connections",
    default_args={"owner": "data", "retries": 0},
    description="Test MySQL and Postgres connections used by mysql_to_postgres",
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["test", "mysql", "postgres"],
) as dag:
    PythonOperator(
        task_id="test_mysql",
        python_callable=test_mysql,
    )
    PythonOperator(
        task_id="test_postgres",
        python_callable=test_postgres,
    )
