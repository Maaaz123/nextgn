"""
DAG: Test MySQL and Dremio connections.

Parameterized via Airflow Variables: environment, mysql_conn_id, dremio_host, dremio_port.
"""
import traceback
from datetime import datetime
import os

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook


def _env():
    return Variable.get("environment", default_var=os.environ.get("AIRFLOW_ENV", "dev"))


def _mysql_conn_id():
    return Variable.get("mysql_conn_id", default_var="mysql_source")


def _dremio_host():
    return Variable.get("dremio_host", default_var=os.environ.get("DREMIO_HOST", "dremio"))


def _dremio_port():
    return int(Variable.get("dremio_port", default_var=os.environ.get("DREMIO_PORT", "9047")))


MYSQL_CONN_ID = _mysql_conn_id()
DREMIO_HOST = _dremio_host()
DREMIO_PORT = _dremio_port()


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


# Tags: environment + layer + domain (connectivity/infra)
_DAG_TAGS = [f"env:{_env()}", "layer:test", "model:connectivity", "domain:connectivity", "test", "mysql", "dremio"]

with DAG(
    dag_id="test_connections",
    default_args={"owner": "data", "retries": 0},
    description="Test MySQL and Dremio connections (lakehouse stack)",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=_DAG_TAGS,
) as dag:
    PythonOperator(
        task_id="test_mysql",
        python_callable=test_mysql,
    )
    PythonOperator(
        task_id="test_dremio",
        python_callable=test_dremio,
    )
