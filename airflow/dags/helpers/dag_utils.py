"""Shared defaults and helpers for landing DAGs."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, List

from airflow.models import Variable

DEFAULT_ARGS = {
    "owner": "data",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}
SCHEDULE = "@hourly"
START_DATE = datetime(2025, 1, 1)


def get_var(key: str, default: str) -> str:
    """Airflow Variable with fallback; use for conn_id, bucket, etc."""
    return Variable.get(key, default_var=default)


def get_env() -> str:
    return get_var("environment", os.environ.get("AIRFLOW_ENV", "dev"))


def get_bucket() -> str:
    return get_var("landing_bucket", os.environ.get("LANDING_BUCKET", "landing"))


def domain_tags(configs: List[Any], table_key: str = "table") -> List[str]:
    """Build domain tags from config list (e.g. domain:plants from table name)."""
    names = {c.get(table_key, "").lower() for c in configs if c.get(table_key)}
    return [f"domain:{n}" for n in sorted(names)]


def api_domain_tags(endpoints: List[Any]) -> List[str]:
    """Build domain tags from API endpoint keys (e.g. api/events -> domain:events)."""
    domains = set()
    for c in endpoints:
        key = (c.get("key") or "").strip("/")
        if key and "/" in key:
            domains.add(key.split("/")[1].lower())
    return [f"domain:{d}" for d in sorted(domains)]


def ingestion_tags(
    source: str,
    configs: List[Any],
    table_key: str = "table",
    extra: List[str] | None = None,
    domain_list: List[str] | None = None,
) -> List[str]:
    """Standard tags for ingestion DAGs: env, layer, model, domain, source, extra."""
    base = [f"env:{get_env()}", "layer:ingestion", "model:landing", f"source:{source}"]
    domains = domain_list if domain_list is not None else domain_tags(configs, table_key)
    rest = (extra or []) + ["minio", "parquet", "landing"]
    return base + domains + rest
