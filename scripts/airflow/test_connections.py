#!/usr/bin/env python3
"""
Test MySQL and Postgres connectivity from the host (no Airflow).

Uses env vars or .env. Run from project root: python scripts/airflow/test_connections.py
Set: MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
     POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
Or create .env with the same (script loads it if python-dotenv is installed).
"""
from __future__ import annotations

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# MySQL
MYSQL_HOST = os.environ.get("MYSQL_HOST", "34.166.142.13")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "mimdbuat01-user")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "mimdbuat01")

# Postgres
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "postgres")


def test_mysql() -> bool:
    try:
        import pymysql
    except ImportError:
        print("MySQL: skip (install PyMySQL: pip install PyMySQL)")
        return True
    if not MYSQL_PASSWORD:
        print("MySQL: skip (set MYSQL_PASSWORD in env or .env to test)")
        return True
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            connect_timeout=10,
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            row = cur.fetchone()
        conn.close()
        print(f"MySQL: OK  host={MYSQL_HOST} db={MYSQL_DATABASE} -> {row}")
        return True
    except Exception as e:
        print(f"MySQL: FAIL  {e}")
        return False


def test_postgres() -> bool:
    try:
        import psycopg2
    except ImportError:
        print("Postgres: skip (install psycopg2: pip install psycopg2-binary)")
        return True
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB,
            connect_timeout=10,
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            row = cur.fetchone()
        conn.close()
        print(f"Postgres: OK  host={POSTGRES_HOST} db={POSTGRES_DB} -> {row}")
        return True
    except Exception as e:
        print(f"Postgres: FAIL  {e}")
        return False


def main() -> int:
    print("Testing connections (from env / .env)...\n")
    ok_mysql = test_mysql()
    ok_pg = test_postgres()
    print("")
    if ok_mysql and ok_pg:
        print("All connections OK.")
        return 0
    print("One or more connections failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
