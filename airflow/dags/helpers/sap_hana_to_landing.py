"""SAP HANA → MinIO landing as Parquet (streaming batches). Credentials from Airflow Connection."""
from __future__ import annotations

from typing import Any, Iterator

import pandas as pd

import hdbcli.dbapi

from airflow.hooks.base import BaseHook

from helpers.landing_io import validate_identifier, write_batched_parquet_to_landing

BATCH_SIZE = 50_000


def _batch_iterator(
    cursor: Any, columns: list, batch_size: int, schema: str, table: str, log: Any
) -> Iterator[pd.DataFrame]:
    total = 0
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        total += len(rows)
        log(f"Read {total} rows from {schema}.{table}")
        yield pd.DataFrame(rows, columns=columns)


def transfer_table_to_parquet(
    sap_hana_conn_id: str,
    schema: str,
    table: str,
    landing_bucket: str = "landing",
    s3_prefix: str | None = None,
    primary_key: str = "id",
    batch_size: int = BATCH_SIZE,
    logger: Any = None,
) -> int:
    """Read SAP HANA table and write Parquet to MinIO. Path: s3://{bucket}/{schema}/{table}/data.parquet"""
    validate_identifier(schema, "schema")
    validate_identifier(table, "table")
    validate_identifier(landing_bucket, "landing_bucket")
    validate_identifier(primary_key, "primary_key")

    def log(msg: str) -> None:
        if logger:
            logger.info(msg)

    conn_obj = BaseHook.get_connection(sap_hana_conn_id)
    port = conn_obj.port or 30015
    conn = hdbcli.dbapi.connect(
        address=conn_obj.host,
        port=int(port),
        user=conn_obj.login,
        password=conn_obj.password,
    )
    cursor = conn.cursor()
    select_sql = f'SELECT * FROM "{schema}"."{table}" ORDER BY "{primary_key}"'
    cursor.execute(select_sql)
    columns = [desc[0] for desc in cursor.description]

    batches = _batch_iterator(cursor, columns, batch_size, schema, table, log)
    try:
        prefix = (s3_prefix or schema).strip("/")
        key = f"{prefix}/{table}/data.parquet"
        return write_batched_parquet_to_landing(
            batches, columns, landing_bucket, key, logger=logger
        )
    finally:
        cursor.close()
        conn.close()
