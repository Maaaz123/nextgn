#!/usr/bin/env bash
# Test DAGs before running: validate parse/import and list DAGs.
# Run from project root. Requires Docker Compose (stack running) or Airflow on PATH.

set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "=== Testing Airflow DAGs ==="

if docker compose exec airflow-webserver true 2>/dev/null; then
  echo "Using Docker: checking DAG import errors..."
  docker compose exec airflow-webserver airflow dags list-import-errors
  ERRORS=$?
  if [ "$ERRORS" -eq 0 ]; then
    echo "No import errors."
  else
    echo "Import errors found (see above). Fix before running the DAG."
    exit 1
  fi
  echo ""
  echo "DAGs:"
  docker compose exec airflow-webserver airflow dags list -o table 2>/dev/null || true
  echo ""
  echo "DAG test OK. You can trigger runs from the UI or: airflow dags trigger <dag_id>"
  exit 0
fi

# No Docker: try local Airflow (e.g. in venv)
if command -v airflow >/dev/null 2>&1; then
  export AIRFLOW_HOME="${AIRFLOW_HOME:-./airflow}"
  export AIRFLOW__CORE__LOAD_EXAMPLES="false"
  echo "Using local Airflow: checking DAG import errors..."
  airflow dags list-import-errors
  echo ""
  airflow dags list -o table 2>/dev/null || true
  echo "DAG test OK."
  exit 0
fi

echo "Docker Compose not running and 'airflow' not on PATH."
echo "Start the stack first: docker compose up -d"
echo "Then run this script again, or run: docker compose exec airflow-webserver airflow dags list-import-errors"
exit 1
