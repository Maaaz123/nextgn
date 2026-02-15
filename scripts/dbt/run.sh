#!/usr/bin/env bash
# Run dbt commands via the Airflow container (Dremio target).
# Usage: ./scripts/dbt/run.sh [dbt command...]   e.g.  ./scripts/dbt/run.sh run | test
# Requires: Docker Compose stack up (docker compose up -d).

set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

ENV_ARGS=(
  -e DREMIO_HOST=dremio
  -e DREMIO_PORT=9047
  -e DREMIO_USER=admin
  -e DREMIO_PASSWORD="${DREMIO_PASSWORD:-Maaz123123123@f}"
  -e DREMIO_OBJECT_STORAGE_SOURCE=minio
  -e DREMIO_OBJECT_STORAGE_PATH=no_schema
)

if ! docker compose exec airflow-scheduler true 2>/dev/null; then
  echo "Error: Airflow stack is not running. Start it with: docker compose up -d"
  exit 1
fi

if [ $# -eq 0 ]; then set -- run; fi
docker compose exec "${ENV_ARGS[@]}" airflow-scheduler bash -c "cd /opt/airflow/dbt && dbt $* --target dremio_dev"
