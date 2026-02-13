#!/bin/bash
# Create databases for Airflow metadata, analytics warehouse, and Metabase metadata
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE DATABASE warehouse;
  CREATE DATABASE airflow;
  CREATE DATABASE metabase;
  GRANT ALL PRIVILEGES ON DATABASE warehouse TO $POSTGRES_USER;
  GRANT ALL PRIVILEGES ON DATABASE airflow TO $POSTGRES_USER;
  GRANT ALL PRIVILEGES ON DATABASE metabase TO $POSTGRES_USER;
EOSQL

# Create raw schema and example table in warehouse for dbt
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d warehouse <<-EOSQL
  CREATE SCHEMA IF NOT EXISTS raw;
  CREATE TABLE IF NOT EXISTS raw.example_events (
    id serial primary key,
    event_at timestamptz not null default now(),
    user_id int,
    event_type text,
    payload jsonb
  );
  INSERT INTO raw.example_events (event_at, user_id, event_type, payload)
  SELECT
    now() - (g || ' hours')::interval,
    (random() * 100)::int,
    (array['page_view', 'signup', 'purchase'])[1 + (random() * 3)::int],
    '{"source": "seed"}'::jsonb
  FROM generate_series(1, 48) g
  ;
EOSQL
