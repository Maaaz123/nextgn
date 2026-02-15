#!/usr/bin/env bash
# Run dbt against Dremio (lakehouse: MinIO + Iceberg + Dremio).
# Set DREMIO_* env vars or use .env. From project root:
#   ./scripts/dbt/run_lakehouse.sh
#   ./scripts/dbt/run_lakehouse.sh run   # run only
set -e
cd "$(dirname "$0")/../.."
[ -f .env ] && set -a && source .env && set +a

export DREMIO_HOST="${DREMIO_HOST:-localhost}"
export DREMIO_PORT="${DREMIO_PORT:-9047}"
export DREMIO_USER="${DREMIO_USER:-dremio}"
export DREMIO_PASSWORD="${DREMIO_PASSWORD:-dremio}"
export DREMIO_OBJECT_STORAGE_SOURCE="${DREMIO_OBJECT_STORAGE_SOURCE:-minio}"
export DREMIO_OBJECT_STORAGE_PATH="${DREMIO_OBJECT_STORAGE_PATH:-no_schema}"
export DREMIO_SPACE="${DREMIO_SPACE:-dbt}"
export DREMIO_SPACE_FOLDER="${DREMIO_SPACE_FOLDER:-public}"

echo "Using Dremio at ${DREMIO_HOST}:${DREMIO_PORT} (object_storage=${DREMIO_OBJECT_STORAGE_SOURCE}/${DREMIO_OBJECT_STORAGE_PATH})"

if command -v dbt >/dev/null 2>&1; then
  dbt deps --project-dir dbt
  if [ -n "$1" ]; then
    dbt "$@" --project-dir dbt --profiles-dir dbt --target dremio_dev
  else
    dbt deps --project-dir dbt --profiles-dir dbt --target dremio_dev
    dbt run --project-dir dbt --profiles-dir dbt --target dremio_dev
    dbt test --project-dir dbt --profiles-dir dbt --target dremio_dev
  fi
else
  echo "Run inside Docker with dbt-dremio: docker compose run --rm airflow-scheduler bash -c 'cd /opt/airflow && DREMIO_HOST=dremio scripts/dbt/run_lakehouse.sh $*'"
  exit 1
fi
