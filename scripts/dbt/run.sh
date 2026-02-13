#!/usr/bin/env bash
# Run dbt commands using the Airflow container (no local dbt install needed).
# Usage: ./scripts/dbt/run.sh [dbt command...]   e.g.  ./scripts/dbt/run.sh debug | deps | run | test
# Requires: Docker Compose stack up (docker compose up -d).

set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

# Pass each env var with its own -e so Docker doesn't treat a value as the service name
ENV_ARGS=(
  -e WAREHOUSE_HOST=postgres
  -e WAREHOUSE_PORT=5432
  -e WAREHOUSE_USER=postgres
  -e WAREHOUSE_PASSWORD=postgres
  -e WAREHOUSE_DB=warehouse
  -e DBT_SCHEMA=public
)

if ! docker compose exec airflow-scheduler true 2>/dev/null; then
  echo "Error: Airflow stack is not running. Start it with: docker compose up -d"
  echo "Then run this script again."
  exit 1
fi

if [ $# -eq 0 ]; then set -- run; fi
docker compose exec "${ENV_ARGS[@]}" airflow-scheduler bash -c "cd /opt/airflow/dbt && dbt $*"
