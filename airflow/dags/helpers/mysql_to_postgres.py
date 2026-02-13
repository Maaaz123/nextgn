"""
MySQL → PostgreSQL table transfer logic.

Supports full refresh (truncate + insert) or incremental load (upsert new/updated rows).
Uses a state table in Postgres to track last sync position per table.
"""
from __future__ import annotations

import re
from typing import Any

from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Safe identifier: alphanumeric and underscore only (prevents SQL injection from Variable)
IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")

BATCH_SIZE = 5000
SYNC_STATE_SCHEMA = "raw"
SYNC_STATE_TABLE = "_sync_state"


def _validate_identifier(name: str, kind: str) -> None:
    if not name or not IDENTIFIER_PATTERN.match(name):
        raise ValueError(f"Invalid {kind}: must be alphanumeric and underscore only, got {name!r}")


# Variable key for simple list: JSON array of table names, same schema for all
TABLE_LIST_VARIABLE_KEY = "mysql_to_postgres_table_list"
MYSQL_SCHEMA_VARIABLE_KEY = "mysql_to_postgres_schema"  # default mimdbuat01
POSTGRES_SCHEMA_VARIABLE_KEY = "mysql_to_postgres_postgres_schema"  # default raw


def get_tables_config(
    variable_key: str = "mysql_to_postgres_tables",
    default_tables: list[dict[str, Any]] | None = None,
    *,
    table_list_variable: str = TABLE_LIST_VARIABLE_KEY,
    mysql_schema_variable: str = MYSQL_SCHEMA_VARIABLE_KEY,
    postgres_schema_variable: str = POSTGRES_SCHEMA_VARIABLE_KEY,
) -> list[dict[str, Any]]:
    """
    Load table mapping from Airflow Variables.

    Option A (full control): Variable `mysql_to_postgres_tables` = JSON array of
    objects with mysql_schema, mysql_table, and optional postgres_schema, postgres_table,
    incremental_column, primary_key.

    Option B (many tables, same schema): Set Variable `mysql_to_postgres_table_list`
    = JSON array of table name strings.
    """
    from airflow.models import Variable

    default_tables = default_tables or []

    # Prefer full config if set
    try:
        config = Variable.get(variable_key, deserialize_json=True)
        if not isinstance(config, list):
            raise ValueError(f"{variable_key} must be a JSON array")
        if config and isinstance(config[0], dict):
            return config
    except KeyError:
        pass
    except (ValueError, TypeError):
        pass

    # Fallback: simple list of table names
    try:
        table_names = Variable.get(table_list_variable, deserialize_json=True)
        if not isinstance(table_names, list):
            raise ValueError(f"{table_list_variable} must be a JSON array of strings")
        mysql_schema = Variable.get(mysql_schema_variable, default_var="mimdbuat01")
        postgres_schema = Variable.get(postgres_schema_variable, default_var="raw")
        return [
            {
                "mysql_schema": mysql_schema,
                "mysql_table": str(t).strip(),
                "postgres_schema": postgres_schema,
                "postgres_table": str(t).strip(),
            }
            for t in table_names
            if str(t).strip()
        ]
    except KeyError:
        return default_tables
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid Airflow Variable for table list: {e}") from e


def _ensure_sync_state_table(pg_hook: PostgresHook) -> None:
    pg_hook.run(
        f"""
        CREATE TABLE IF NOT EXISTS "{SYNC_STATE_SCHEMA}"."{SYNC_STATE_TABLE}" (
            mysql_schema TEXT NOT NULL,
            mysql_table  TEXT NOT NULL,
            incremental_column TEXT NOT NULL,
            last_value   TEXT,
            updated_at   TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (mysql_schema, mysql_table)
        )
        """
    )


def _get_last_value(
    pg_hook: PostgresHook,
    mysql_schema: str,
    mysql_table: str,
    incremental_column: str,
) -> str | None:
    """Return last_value for this table from state table, or None if first run."""
    pg_hook.run(f'CREATE SCHEMA IF NOT EXISTS "{SYNC_STATE_SCHEMA}"')
    _ensure_sync_state_table(pg_hook)
    conn = pg_hook.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT last_value FROM "raw"."_sync_state"
                WHERE mysql_schema = %s AND mysql_table = %s
                """,
                (mysql_schema, mysql_table),
            )
            row = cur.fetchone()
            return row[0] if row and row[0] else None
    finally:
        conn.close()


def _set_last_value(
    pg_hook: PostgresHook,
    mysql_schema: str,
    mysql_table: str,
    incremental_column: str,
    last_value: str,
) -> None:
    conn = pg_hook.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO "raw"."_sync_state" (mysql_schema, mysql_table, incremental_column, last_value, updated_at)
                VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (mysql_schema, mysql_table)
                DO UPDATE SET incremental_column = EXCLUDED.incremental_column, last_value = EXCLUDED.last_value, updated_at = now()
                """,
                (mysql_schema, mysql_table, incremental_column, last_value),
            )
        conn.commit()
    finally:
        conn.close()


def _ensure_primary_key(
    pg_conn: Any,
    postgres_schema: str,
    postgres_table: str,
    primary_key: str,
) -> None:
    """Ensure target table has PRIMARY KEY on primary_key so ON CONFLICT works."""
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE n.nspname = %s AND t.relname = %s AND c.contype = 'p'
            """,
            (postgres_schema, postgres_table),
        )
        if cur.fetchone():
            return
        # Add primary key (table may have been created earlier without it)
        try:
            cur.execute(
                f'ALTER TABLE "{postgres_schema}"."{postgres_table}" '
                f'ADD PRIMARY KEY ("{primary_key}")'
            )
            pg_conn.commit()
        except Exception as e:
            pg_conn.rollback()
            raise RuntimeError(
                f"Table {postgres_schema}.{postgres_table} has no PRIMARY KEY and adding one failed (e.g. duplicates on {primary_key}). "
                "Drop the table and re-run, or fix duplicates."
            ) from e


def transfer_table(
    mysql_conn_id: str,
    postgres_conn_id: str,
    mysql_schema: str,
    mysql_table: str,
    postgres_schema: str = "raw",
    postgres_table: str | None = None,
    batch_size: int = BATCH_SIZE,
    incremental_column: str | None = None,
    primary_key: str = "id",
    logger: Any = None,
) -> int:
    """
    Sync MySQL table to Postgres.

    - If incremental_column is set (e.g. "updated_at"): load only rows where
      incremental_column > last_value from state table; upsert into Postgres by primary_key.
      First run (no state): full load then set state.
    - If incremental_column is not set: full refresh (truncate + insert).

    primary_key is used for ON CONFLICT when doing incremental upsert.
    """
    _validate_identifier(mysql_schema, "mysql_schema")
    _validate_identifier(mysql_table, "mysql_table")
    _validate_identifier(postgres_schema, "postgres_schema")
    postgres_table = postgres_table or mysql_table
    _validate_identifier(postgres_table, "postgres_table")
    if incremental_column:
        _validate_identifier(incremental_column, "incremental_column")
    _validate_identifier(primary_key, "primary_key")

    def log(msg: str) -> None:
        if logger:
            logger.info(msg)

    mysql_hook = MySqlHook(mysql_conn_id=mysql_conn_id, schema=mysql_schema)
    pg_hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    # Log target DB so you can confirm in Airflow task logs (Schema = database name in Postgres connection)
    try:
        pg_conn_obj = pg_hook.get_connection(postgres_conn_id)
        log(f"Postgres target: host={pg_conn_obj.host} database(schema field)={getattr(pg_conn_obj, 'schema', '')} → tables in schema '{postgres_schema}'")
    except Exception:
        pass
    pg_hook.run(f'CREATE SCHEMA IF NOT EXISTS "{postgres_schema}"')

    # ---- Determine query and mode ----
    last_value = None
    if incremental_column:
        last_value = _get_last_value(pg_hook, mysql_schema, mysql_table, incremental_column)

    mysql_conn = mysql_hook.get_conn()
    try:
        cursor = mysql_conn.cursor()
        try:
            if incremental_column and last_value is not None:
                # Incremental: only new/updated rows
                select_sql = (
                    f"SELECT * FROM `{mysql_table}` WHERE `{incremental_column}` > %s ORDER BY `{incremental_column}`"
                )
                cursor.execute(select_sql, (last_value,))
            else:
                # Full load (first run or no incremental)
                select_sql = f"SELECT * FROM `{mysql_table}` ORDER BY `{incremental_column or primary_key}`"
                cursor.execute(select_sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
        finally:
            cursor.close()
    finally:
        mysql_conn.close()

    row_count = len(rows)
    if row_count == 0 and incremental_column and last_value is not None:
        log(f"Incremental: no new/updated rows for {mysql_schema}.{mysql_table} (last_value={last_value})")
        return 0

    if row_count == 0:
        log(f"Source {mysql_schema}.{mysql_table} is empty; ensuring target table exists.")
        pg_conn = pg_hook.get_conn()
        try:
            with pg_conn.cursor() as pg_cursor:
                create_cols = ", ".join(f'"{c}" TEXT' for c in columns)
                pg_cursor.execute(
                    f'CREATE TABLE IF NOT EXISTS "{postgres_schema}"."{postgres_table}" ({create_cols})'
                )
            pg_conn.commit()
        finally:
            pg_conn.close()
        return 0

    # ---- Build DDL/DML ----
    col_list = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join("%s" for _ in columns)
    # With incremental we need PRIMARY KEY for ON CONFLICT
    if primary_key in columns:
        create_cols = ", ".join(
            f'"{c}" TEXT PRIMARY KEY' if c == primary_key else f'"{c}" TEXT' for c in columns
        )
    else:
        create_cols = ", ".join(f'"{c}" TEXT' for c in columns)

    use_upsert = incremental_column and (last_value is not None or row_count > 0)
    if use_upsert:
        # INSERT ... ON CONFLICT (pk) DO UPDATE SET col=EXCLUDED.col ...
        set_parts = [f'"{c}" = EXCLUDED."{c}"' for c in columns if c != primary_key]
        if not set_parts:
            set_parts = [f'"{primary_key}" = EXCLUDED."{primary_key}"']
        upsert_sql = (
            f'INSERT INTO "{postgres_schema}"."{postgres_table}" ({col_list}) VALUES ({placeholders})'
            f' ON CONFLICT ("{primary_key}") DO UPDATE SET {", ".join(set_parts)}'
        )
    else:
        upsert_sql = f'INSERT INTO "{postgres_schema}"."{postgres_table}" ({col_list}) VALUES ({placeholders})'

    pg_conn = pg_hook.get_conn()
    try:
        with pg_conn.cursor() as pg_cursor:
            pg_cursor.execute(
                f'CREATE TABLE IF NOT EXISTS "{postgres_schema}"."{postgres_table}" ({create_cols})'
            )
            pg_conn.commit()

            if use_upsert:
                # Existing table may have been created without PK; ensure it for ON CONFLICT
                _ensure_primary_key(pg_conn, postgres_schema, postgres_table, primary_key)
                try:
                    for offset in range(0, row_count, batch_size):
                        batch = rows[offset : offset + batch_size]
                        pg_cursor.executemany(upsert_sql, batch)
                    pg_conn.commit()
                except Exception as e:
                    err_msg = str(e).lower()
                    if "unique" in err_msg or "constraint" in err_msg or "conflict" in err_msg:
                        pg_conn.rollback()
                        # Fallback: truncate and insert so data still lands
                        log(f"Upsert failed ({e}), falling back to truncate + insert")
                        pg_cursor.execute(f'TRUNCATE TABLE "{postgres_schema}"."{postgres_table}"')
                        pg_conn.commit()
                        insert_only = f'INSERT INTO "{postgres_schema}"."{postgres_table}" ({col_list}) VALUES ({placeholders})'
                        for offset in range(0, row_count, batch_size):
                            batch = rows[offset : offset + batch_size]
                            pg_cursor.executemany(insert_only, batch)
                        pg_conn.commit()
                    else:
                        raise
            else:
                pg_cursor.execute(f'TRUNCATE TABLE "{postgres_schema}"."{postgres_table}"')
                pg_conn.commit()
                for offset in range(0, row_count, batch_size):
                    batch = rows[offset : offset + batch_size]
                    pg_cursor.executemany(upsert_sql, batch)
                pg_conn.commit()

            # Update state for incremental
            if incremental_column and row_count > 0:
                # Max value of incremental column in this batch (last row due to ORDER BY)
                inc_col_idx = columns.index(incremental_column)
                max_val = rows[-1][inc_col_idx]
                max_val_str = str(max_val) if max_val is not None else None
                if max_val_str:
                    _set_last_value(pg_hook, mysql_schema, mysql_table, incremental_column, max_val_str)
    finally:
        pg_conn.close()

    mode = "incremental (upsert)" if use_upsert else "full refresh"
    log(f"Synced {row_count} rows ({mode}): {mysql_schema}.{mysql_table} → {postgres_schema}.{postgres_table}")
    return row_count
