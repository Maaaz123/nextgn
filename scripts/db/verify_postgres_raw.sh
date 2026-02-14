#!/usr/bin/env bash
# Verify raw schema and MySQL-synced tables. Run from project root.
# Usage: ./scripts/db/verify_postgres_raw.sh [database_name]
#   No arg: check both warehouse and postgres (mysql_to_postgres can write to either)
#   warehouse | postgres: check only that database

set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

check_db() {
  local DB="$1"
  echo ""
  echo "=== Database: $DB ==="
  if ! docker compose exec postgres psql -U postgres -d "$DB" -c "
    SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'raw';
  " 2>/dev/null; then
    echo "  (no raw schema or cannot connect)"
    return 1
  fi
  echo ""
  echo "Tables in raw:"
  docker compose exec postgres psql -U postgres -d "$DB" -c "
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_schema = 'raw'
    ORDER BY table_schema, table_name;
  " 2>/dev/null || true
  echo ""
  echo "Row counts:"
  for t in flows plants licenses _sync_state; do
    n=$(docker compose exec postgres psql -U postgres -d "$DB" -t -A -c "SELECT count(*) FROM raw.\"$t\";" 2>/dev/null) || n="(missing)"
    echo "  raw.$t: $n"
  done
}

if [ -n "$1" ]; then
  check_db "$1"
else
  echo "Checking both warehouse and postgres (mysql_to_postgres writes to whichever Schema you set in postgres_warehouse):"
  check_db warehouse
  check_db postgres
fi

echo ""
echo "Tip: In Airflow Admin → Connections, postgres_warehouse Schema = database name."
echo "  Schema=warehouse → raw tables in warehouse DB. Schema=postgres → raw tables in postgres DB."
