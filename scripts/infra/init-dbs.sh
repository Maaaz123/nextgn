#!/bin/bash
# Create databases for Airflow metadata and Metabase (when using docker-compose.postgres.yml)
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE DATABASE airflow;
  CREATE DATABASE metabase;
  GRANT ALL PRIVILEGES ON DATABASE airflow TO $POSTGRES_USER;
  GRANT ALL PRIVILEGES ON DATABASE metabase TO $POSTGRES_USER;
EOSQL
