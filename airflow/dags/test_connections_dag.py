"""
DAG: Test MySQL and Dremio connections (mysql_source, dremio).

Run this DAG to verify connections before running ingestion or data_pipeline_lakehouse.
Create mysql_source in Admin → Connections (see airflow/CONNECTIONS.md).
Dremio is reached at host dremio:9047 by default (no connection required).
"""
import traceback
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook

MYSQL_CONN_ID = "mysql_source"
DREMIO_HOST = "dremio"
DREMIO_PORT = 9047


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


def test_dremio(**context):
    ti = context["ti"]
    ti.log.info("Testing Dremio at %s:%s", DREMIO_HOST, DREMIO_PORT)
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((DREMIO_HOST, DREMIO_PORT))
        s.close()
        msg = f"Dremio OK: {DREMIO_HOST}:{DREMIO_PORT} (reachable)"
        ti.log.info(msg)
        return msg
    except Exception as e:
        ti.log.error("Dremio connection failed: %s", e)
        ti.log.error(traceback.format_exc())
        raise


with DAG(
    dag_id="test_connections",
    default_args={"owner": "data", "retries": 0},
    description="Test MySQL and Dremio connections (lakehouse stack)",
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["test", "mysql", "dremio"],
) as dag:
    PythonOperator(
        task_id="test_mysql",
        python_callable=test_mysql,
    )
    PythonOperator(
        task_id="test_dremio",
        python_callable=test_dremio,
    )
