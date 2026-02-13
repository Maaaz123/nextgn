#!/usr/bin/env bash
# Verify that database "postgres" has schema "raw" and list tables there.
# Run from project root. Uses docker compose postgres or local psql.
# Usage: ./scripts/db/verify_postgres_raw.sh [database_name]
# Default database: postgres

set -e
DB="${1:-postgres}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "=== Checking database '$DB' for schema 'raw' and tables ==="

if docker compose exec postgres psql -U postgres -d "$DB" -c "
  SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'raw';
" 2>/dev/null; then
  echo ""
  echo "Tables in raw schema:"
  docker compose exec postgres psql -U postgres -d "$DB" -c "
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_schema = 'raw'
    ORDER BY table_schema, table_name;
  "
  echo ""
  echo "Row counts:"
  for t in flows plants licenses; do
    n=$(docker compose exec postgres psql -U postgres -d "$DB" -t -A -c "SELECT count(*) FROM raw.$t;" 2>/dev/null) || n="(table missing)"
    echo "  raw.$t: $n"
  done
else
  echo "Could not connect. Start stack: docker compose up -d"
  echo "Then ensure Airflow connection postgres_warehouse has Schema = postgres"
  exit 1
fi
