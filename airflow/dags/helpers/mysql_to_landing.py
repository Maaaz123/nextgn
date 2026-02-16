"""MySQL → MinIO landing as Parquet (streaming batches)."""
from __future__ import annotations

from typing import Any, Iterator

import pandas as pd

from airflow.providers.mysql.hooks.mysql import MySqlHook

from helpers.landing_io import (
    validate_identifier as _validate_identifier,
    write_batched_parquet_to_landing,
)

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
    mysql_conn_id: str,
    mysql_schema: str,
    mysql_table: str,
    landing_bucket: str = "landing",
    s3_prefix: str | None = None,
    primary_key: str | None = "id",
    batch_size: int = BATCH_SIZE,
    logger: Any = None,
) -> int:
    """Read MySQL table and write Parquet to MinIO. Path: s3://{bucket}/{schema}/{table}/data.parquet"""
    _validate_identifier(mysql_schema, "mysql_schema")
    _validate_identifier(mysql_table, "mysql_table")
    _validate_identifier(landing_bucket, "landing_bucket")
    if primary_key:
        _validate_identifier(primary_key, "primary_key")

    def log(msg: str) -> None:
        if logger:
            logger.info(msg)

    hook = MySqlHook(mysql_conn_id=mysql_conn_id, schema=mysql_schema)
    conn = hook.get_conn()
    cursor = conn.cursor()
    order_clause = f" ORDER BY `{primary_key}`" if primary_key else ""
    select_sql = f"SELECT * FROM `{mysql_table}`{order_clause}"
    cursor.execute(select_sql)
    columns = [desc[0] for desc in cursor.description]

    batches = _batch_iterator(
        cursor, columns, batch_size, mysql_schema, mysql_table, log
    )
    try:
        prefix = (s3_prefix or mysql_schema).strip("/")
        key = f"{prefix}/{mysql_table}/data.parquet"
        return write_batched_parquet_to_landing(
            batches, columns, landing_bucket, key, logger=logger
        )
    finally:
        cursor.close()
        conn.close()
