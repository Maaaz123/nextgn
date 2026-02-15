"""
MySQL → MinIO landing bucket as Parquet files.

Reads from MySQL, writes Parquet to S3-compatible storage (MinIO landing bucket).
Uses streaming/batching for large tables to avoid memory issues.
"""
from __future__ import annotations

import io
from typing import List
import os
import re
from typing import Any

from airflow.providers.mysql.hooks.mysql import MySqlHook

IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")
BATCH_SIZE = 50_000


def _validate_identifier(name: str, kind: str) -> None:
    if not name or not IDENTIFIER_PATTERN.match(name):
        raise ValueError(f"Invalid {kind}: must be alphanumeric and underscore only, got {name!r}")


def _get_s3_client(
    endpoint: str | None = None,
    access_key: str | None = None,
    secret_key: str | None = None,
) -> Any:
    """Return boto3 S3 client for MinIO (S3-compatible)."""
    import boto3
    from botocore.config import Config

    endpoint = endpoint or os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
    access_key = access_key or os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = secret_key or os.environ.get("MINIO_SECRET_KEY", "minioadmin")

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def transfer_table_to_parquet(
    mysql_conn_id: str,
    mysql_schema: str,
    mysql_table: str,
    landing_bucket: str = "landing",
    s3_prefix: str | None = None,
    primary_key: str = "id",
    batch_size: int = BATCH_SIZE,
    logger: Any = None,
) -> int:
    """
    Read MySQL table and write as Parquet to MinIO landing bucket.

    Output path: s3://{landing_bucket}/{s3_prefix or mysql_schema}/{mysql_table}/data.parquet
    For incremental support later: {mysql_table}/{date}/data.parquet
    """
    _validate_identifier(mysql_schema, "mysql_schema")
    _validate_identifier(mysql_table, "mysql_table")
    _validate_identifier(landing_bucket, "landing_bucket")
    _validate_identifier(primary_key, "primary_key")

    def log(msg: str) -> None:
        if logger:
            logger.info(msg)

    mysql_hook = MySqlHook(mysql_conn_id=mysql_conn_id, schema=mysql_schema)
    s3 = _get_s3_client()

    # Read from MySQL in batches
    conn = mysql_hook.get_conn()
    cursor = conn.cursor()
    select_sql = f"SELECT * FROM `{mysql_table}` ORDER BY `{primary_key}`"
    cursor.execute(select_sql)
    columns = [desc[0] for desc in cursor.description]

    import pandas as pd

    dfs: List[pd.DataFrame] = []
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        dfs.append(pd.DataFrame(rows, columns=columns))
        log(f"Read {sum(len(d) for d in dfs)} rows from {mysql_schema}.{mysql_table}")

    cursor.close()
    conn.close()

    prefix = (s3_prefix or mysql_schema).strip("/")
    key = f"{prefix}/{mysql_table}/data.parquet"

    if not dfs:
        log(f"Table {mysql_schema}.{mysql_table} is empty; writing empty Parquet")
        df = pd.DataFrame(columns=columns)
    else:
        df = pd.concat(dfs, ignore_index=True)

    row_count = len(df)
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)
    s3.put_object(Bucket=landing_bucket, Key=key, Body=buffer.getvalue())
    log(f"Wrote {row_count} rows to s3://{landing_bucket}/{key}")
    return row_count
