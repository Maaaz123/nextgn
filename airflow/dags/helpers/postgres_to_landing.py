"""PostgreSQL → MinIO landing as Parquet (streaming batches)."""
from __future__ import annotations

from typing import Any, Iterator

import pandas as pd

from airflow.providers.postgres.hooks.postgres import PostgresHook

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
    postgres_conn_id: str,
    schema: str,
    table: str,
    landing_bucket: str = "landing",
    s3_prefix: str | None = None,
    primary_key: str = "id",
    batch_size: int = BATCH_SIZE,
    logger: Any = None,
) -> int:
    """Read Postgres table and write Parquet to MinIO. Path: s3://{bucket}/{schema}/{table}/data.parquet"""
    validate_identifier(schema, "schema")
    validate_identifier(table, "table")
    validate_identifier(landing_bucket, "landing_bucket")
    validate_identifier(primary_key, "primary_key")

    def log(msg: str) -> None:
        if logger:
            logger.info(msg)

    hook = PostgresHook(postgres_conn_id=postgres_conn_id, schema=schema)
    conn = hook.get_conn()
    cursor = conn.cursor()
    select_sql = f'SELECT * FROM "{schema}"."{table}" ORDER BY "{primary_key}"'
    cursor.execute(select_sql)
    columns = [d[0] for d in cursor.description]

    batches = _batch_iterator(cursor, columns, batch_size, schema, table, log)
    try:
        key = f"{(s3_prefix or schema).strip('/')}/{table}/data.parquet"
        return write_batched_parquet_to_landing(
            batches, columns, landing_bucket, key, logger=logger
        )
    finally:
        cursor.close()
        conn.close()
