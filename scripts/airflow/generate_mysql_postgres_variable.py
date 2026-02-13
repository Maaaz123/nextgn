#!/usr/bin/env python3
"""
Generate Airflow Variable JSON for mysql_to_postgres DAG.

Usage (from project root):
  # From a file (one table name per line)
  python scripts/airflow/generate_mysql_postgres_variable.py tables.txt

  # From stdin
  echo -e "flows\nusers\norders" | python scripts/airflow/generate_mysql_postgres_variable.py

  # Custom schema
  python scripts/airflow/generate_mysql_postgres_variable.py tables.txt --mysql-schema mydb --postgres-schema raw

Output: JSON array for Variable "mysql_to_postgres_tables" (or simple list for "mysql_to_postgres_table_list").
"""
from __future__ import annotations

import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate mysql_to_postgres Variable JSON")
    parser.add_argument(
        "file",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="File with one table name per line (default: stdin)",
    )
    parser.add_argument("--mysql-schema", default="mimdbuat01", help="MySQL schema/database name")
    parser.add_argument("--postgres-schema", default="raw", help="Postgres schema name")
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Output simple JSON array of names (for Variable mysql_to_postgres_table_list)",
    )
    args = parser.parse_args()

    with args.file as f:
        names = [line.strip() for line in f if line.strip()]

    if not names:
        print("No table names read.", file=sys.stderr)
        sys.exit(1)

    if args.simple:
        print(json.dumps(names, indent=2))
        return

    config = [
        {
            "mysql_schema": args.mysql_schema,
            "mysql_table": name,
            "postgres_schema": args.postgres_schema,
            "postgres_table": name,
        }
        for name in names
    ]
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
