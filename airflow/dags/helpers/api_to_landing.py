"""API → MinIO landing as Parquet (or JSON for non-tabular responses)."""
from __future__ import annotations

import io
from typing import Any, Optional
import pandas as pd
import requests

from helpers.landing_io import validate_identifier, get_s3_client, write_dataframe_to_landing, write_json_to_landing


def _parquet_key(key: str) -> str:
    """Normalize key to end with .parquet."""
    key = key.strip("/").rstrip("/")
    if key.endswith(".parquet"):
        return key
    if key.endswith(".json"):
        return key[: -len(".json")] + ".parquet"
    return f"{key}.parquet" if key else "data.parquet"


def _auth_header_from_variable(auth_variable: Optional[str]) -> dict:
    """Authorization header from Airflow Variable (value: 'Bearer <token>' or '<token>')."""
    if not auth_variable:
        return {}
    try:
        from airflow.models import Variable
        value = Variable.get(auth_variable, default_var=None)
        if not value:
            return {}
        value = value.strip()
        if value.lower().startswith("bearer ") or value.lower().startswith("apikey "):
            return {"Authorization": value}
        return {"Authorization": f"Bearer {value}"}
    except Exception:
        return {}


def fetch_api_to_landing(
    url: str,
    landing_bucket: str,
    key: str,
    method: str = "GET",
    headers: Optional[dict] = None,
    auth_variable: Optional[str] = None,
    output_format: str = "parquet",
    logger: Any = None,
) -> int:
    """Fetch API and write to MinIO (Parquet if tabular, else JSON). auth_variable = Variable name for token."""
    validate_identifier(landing_bucket, "landing_bucket")

    def log(msg: str) -> None:
        if logger:
            logger.info(msg)

    h = dict(headers or {})
    h.update(_auth_header_from_variable(auth_variable))

    log(f"Fetching {method} {url}")
    resp = requests.request(
        method=method,
        url=url,
        headers=h,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    # Prefer Parquet for landing: write Parquet whenever response is tabular (list of objects)
    is_tabular = isinstance(data, list) and data and isinstance(data[0], dict)
    if is_tabular and output_format != "json":
        df = pd.DataFrame(data)
        parquet_key = _parquet_key(key)
        n = write_dataframe_to_landing(df, landing_bucket, parquet_key, logger=logger, format="parquet")
        log(f"Wrote {n} rows to s3://{landing_bucket}/{parquet_key} (parquet)")
        return n
    # Non-tabular or explicit output_format=json → write JSON
    write_json_to_landing(data, landing_bucket, key, logger=logger)
    return 1
