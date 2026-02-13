"""
Tests for MySQL → Postgres helper (config, validation).
Run from project root: pytest tests/ -v
No real DB or Airflow runtime required when using mocks.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add airflow/dags so we can import helpers
_dags_dir = Path(__file__).resolve().parent.parent / "airflow" / "dags"
if _dags_dir.exists():
    sys.path.insert(0, str(_dags_dir))

from helpers.mysql_to_postgres import (
    IDENTIFIER_PATTERN,
    get_tables_config,
    TABLE_LIST_VARIABLE_KEY,
)


def test_identifier_pattern():
    assert IDENTIFIER_PATTERN.match("flows")
    assert IDENTIFIER_PATTERN.match("raw")
    assert IDENTIFIER_PATTERN.match("mimdbuat01")
    assert IDENTIFIER_PATTERN.match("table_name")
    assert not IDENTIFIER_PATTERN.match("")
    assert not IDENTIFIER_PATTERN.match("table-name")
    assert not IDENTIFIER_PATTERN.match("a; DROP TABLE x;--")


# Default tables we expect when no Variable is set
EXPECTED_DEFAULT_KEYS = {"mysql_schema", "mysql_table", "postgres_schema", "postgres_table"}


@patch("airflow.models.Variable")
def test_get_tables_config_returns_default_when_no_variable(mock_var):
    mock_var.get.side_effect = KeyError("mysql_to_postgres_tables")
    default = [
        {"mysql_schema": "mimdbuat01", "mysql_table": "flows", "postgres_schema": "raw", "postgres_table": "flows"},
    ]
    result = get_tables_config(default_tables=default)
    assert result == default


@patch("airflow.models.Variable")
def test_get_tables_config_returns_full_config_from_variable(mock_var):
    config = [
        {"mysql_schema": "mimdbuat01", "mysql_table": "flows", "postgres_schema": "raw", "postgres_table": "flows"},
    ]
    mock_var.get.return_value = config
    result = get_tables_config(variable_key="mysql_to_postgres_tables", default_tables=[])
    assert result == config
    mock_var.get.assert_called_with("mysql_to_postgres_tables", deserialize_json=True)


@patch("airflow.models.Variable")
def test_get_tables_config_expands_table_list_variable(mock_var):
    # First call returns KeyError (no full config), second returns table list, then schema vars
    mock_var.get.side_effect = [
        KeyError("mysql_to_postgres_tables"),
        ["flows", "plants"],
        "mimdbuat01",
        "raw",
    ]
    result = get_tables_config(
        variable_key="mysql_to_postgres_tables",
        default_tables=[],
        table_list_variable=TABLE_LIST_VARIABLE_KEY,
    )
    assert len(result) == 2
    assert result[0]["mysql_schema"] == "mimdbuat01"
    assert result[0]["mysql_table"] == "flows"
    assert result[0]["postgres_schema"] == "raw"
    assert result[0]["postgres_table"] == "flows"
    assert result[1]["mysql_table"] == "plants"


def test_dag_default_tables_structure():
    """Ensure DAG default table configs have required keys and valid identifiers."""
    try:
        import mysql_to_postgres_dag as dag_module  # noqa: E402
    except ImportError as e:
        pytest.skip(f"Need Airflow and dags on path to load DAG: {e}")

    for cfg in dag_module.DEFAULT_TABLES:
        for key in EXPECTED_DEFAULT_KEYS:
            assert key in cfg, f"Missing key {key} in {cfg}"
        assert IDENTIFIER_PATTERN.match(cfg["mysql_schema"]), f"Invalid mysql_schema: {cfg}"
        assert IDENTIFIER_PATTERN.match(cfg["mysql_table"]), f"Invalid mysql_table: {cfg}"
        assert IDENTIFIER_PATTERN.match(cfg["postgres_schema"]), f"Invalid postgres_schema: {cfg}"
        assert IDENTIFIER_PATTERN.match(cfg["postgres_table"]), f"Invalid postgres_table: {cfg}"
        if cfg.get("incremental_column"):
            assert IDENTIFIER_PATTERN.match(cfg["incremental_column"])
        if cfg.get("primary_key"):
            assert IDENTIFIER_PATTERN.match(cfg["primary_key"])
