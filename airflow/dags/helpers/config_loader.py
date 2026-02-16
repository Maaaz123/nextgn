"""Load table/endpoint config from dags/config/*.json or Airflow Variable."""
from __future__ import annotations

import json
import logging
import os
from typing import Any, List, Optional

_log = logging.getLogger(__name__)


def _config_dir() -> str:
    helpers_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(helpers_dir), "config")


def _validate_items(data: List[Any], required_keys: Optional[List[str]], context: str) -> None:
    """Validate each config item has required keys. Raises ValueError on first missing."""
    if not required_keys:
        return
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"{context} item {i}: expected dict, got {type(item).__name__}")
        missing = [k for k in required_keys if not item.get(k)]
        if missing:
            raise ValueError(
                f"{context} item {i} missing required keys: {missing}; keys: {list(item.keys())}"
            )


def load_json_config(
    filename: str,
    variable_name: str,
    default: List[Any],
    required_keys: Optional[List[str]] = None,
) -> List[Any]:
    """Load JSON list from file (dags/config/<filename>) or Variable; fallback to default.
    If required_keys given, validates each item has those keys.
    """
    path = os.path.join(_config_dir(), filename)
    data: List[Any] = default

    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                data = loaded
            elif isinstance(loaded, dict):
                data = loaded.get("tables", loaded.get("endpoints", default))
        except OSError as e:
            _log.debug("Config file %s not readable: %s", path, e)
        except json.JSONDecodeError as e:
            _log.warning("Invalid JSON in config %s: %s", path, e)

    if data == default:
        try:
            from airflow.models import Variable

            raw = Variable.get(variable_name, default_var=None)
            if raw:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    data = parsed
                elif isinstance(parsed, dict):
                    data = parsed.get("tables", parsed.get("endpoints", default))
        except json.JSONDecodeError as e:
            _log.warning("Invalid JSON in Variable %s: %s", variable_name, e)
        except Exception as e:
            _log.debug("Variable %s fallback: %s", variable_name, e)

    _validate_items(data, required_keys, filename)
    return data
