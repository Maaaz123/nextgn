"""MinIO (S3-compatible) I/O for landing: Parquet and JSON."""
from __future__ import annotations

import io
import json
import os
import re
from typing import Any, Iterator

import pandas as pd

IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")


def validate_identifier(name: str, kind: str) -> None:
    if not name or not IDENTIFIER_PATTERN.match(name):
        raise ValueError(f"Invalid {kind}: alphanumeric, underscore, dot, hyphen only; got {name!r}")


def _promote_schema_for_batches(schema: "pa.Schema") -> "pa.Schema":
    """Promote int64 to float64 so batches with mixed nulls share a common schema."""
    import pyarrow as pa

    fields = []
    for i in range(len(schema)):
        f = schema.field(i)
        if pa.types.is_integer(f.type):
            fields.append(pa.field(f.name, pa.float64(), f.nullable))
        else:
            fields.append(f)
    return pa.schema(fields)


def write_batched_parquet_to_landing(
    batch_iterator: Iterator[Any],
    columns: list,
    landing_bucket: str,
    key: str,
    logger: Any = None,
) -> int:
    """Stream DataFrame batches to single Parquet in MinIO. Memory-efficient for large tables."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    s3 = get_s3_client()
    buffer = io.BytesIO()
    writer = None
    unified_schema = None
    total = 0

    for df in batch_iterator:
        if df is None or len(df) == 0:
            continue
        table = pa.Table.from_pandas(df, preserve_index=False)
        if writer is None:
            unified_schema = _promote_schema_for_batches(table.schema)
            writer = pq.ParquetWriter(buffer, unified_schema)
        table = table.cast(unified_schema)
        writer.write_table(table)
        total += len(df)
        if logger:
            logger.info(f"Streamed {total} rows to buffer for s3://{landing_bucket}/{key}")

    if writer is not None:
        writer.close()
        buffer.seek(0)
        if logger:
            logger.info(f"Writing {total} rows to s3://{landing_bucket}/{key}")
        s3.put_object(Bucket=landing_bucket, Key=key, Body=buffer.getvalue())
        return total

    return write_dataframe_to_landing(
        pd.DataFrame(columns=columns), landing_bucket, key, logger=logger
    )


def get_s3_client(
    endpoint: str | None = None,
    access_key: str | None = None,
    secret_key: str | None = None,
) -> Any:
    """Boto3 S3 client for MinIO. Uses Variables minio_* or env MINIO_*."""
    import boto3
    from botocore.config import Config

    try:
        from airflow.models import Variable
        _v = lambda k, d: Variable.get(k, default_var=d)
        endpoint = endpoint or _v("minio_endpoint", None) or os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
        access_key = access_key or _v("minio_access_key", None) or os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = secret_key or _v("minio_secret_key", None) or os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    except Exception:
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


def write_dataframe_to_landing(
    df: Any,
    landing_bucket: str,
    key: str,
    logger: Any = None,
    format: str = "parquet",
) -> int:
    """Write DataFrame to MinIO as Parquet (or JSON). Returns row count."""
    s3 = get_s3_client()
    if logger:
        logger.info(f"Writing {len(df)} rows to s3://{landing_bucket}/{key}")
    buffer = io.BytesIO()
    if format == "parquet":
        df.to_parquet(buffer, index=False, engine="pyarrow")
    else:
        buffer.write(df.to_json(orient="records", date_format="iso", lines=False).encode("utf-8"))
    buffer.seek(0)
    s3.put_object(Bucket=landing_bucket, Key=key, Body=buffer.getvalue())
    return len(df)


def write_json_to_landing(data: dict | list, landing_bucket: str, key: str, logger: Any = None) -> None:
    """Write JSON to MinIO landing bucket."""
    s3 = get_s3_client()
    if logger:
        logger.info(f"Writing JSON to s3://{landing_bucket}/{key}")
    body = json.dumps(data, default=str).encode("utf-8")
    s3.put_object(Bucket=landing_bucket, Key=key, Body=body)
