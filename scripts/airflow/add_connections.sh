#!/usr/bin/env bash
# Add Airflow connections for mysql_source and postgres_warehouse.
# Run from project root. Requires: docker compose up, MYSQL_PASSWORD in env or .env.
set -e

cd "$(dirname "$0")/../.."
[ -f .env ] && set -a && source .env && set +a

# Postgres (inside Docker, use host=postgres)
docker compose exec airflow-scheduler airflow connections add postgres_warehouse \
  --conn-type postgres \
  --conn-host postgres \
  --conn-schema postgres \
  --conn-login postgres \
  --conn-password "${POSTGRES_PASSWORD:-postgres}" \
  --conn-port 5432 \
  2>/dev/null || true  # ignore if already exists

# MySQL (requires MYSQL_PASSWORD)
if [ -z "${MYSQL_PASSWORD}" ]; then
  echo "Skipping mysql_source: set MYSQL_PASSWORD in env or .env"
  echo "Then run: MYSQL_PASSWORD=xxx $0"
  exit 0
fi

docker compose exec -e MYSQL_PASSWORD airflow-scheduler airflow connections add mysql_source \
  --conn-type mysql \
  --conn-host "${MYSQL_HOST:-34.166.142.13}" \
  --conn-schema "${MYSQL_DATABASE:-mimdbuat01}" \
  --conn-login "${MYSQL_USER:-mimdbuat01-user}" \
  --conn-password "${MYSQL_PASSWORD}" \
  --conn-port "${MYSQL_PORT:-3306}" \
  2>/dev/null || echo "mysql_source may already exist; update in Admin → Connections if needed"

echo "Connections ready. Trigger test_connections DAG to verify."
