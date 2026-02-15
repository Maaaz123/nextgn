# Lakehouse: MinIO + Apache Iceberg + Dremio + dbt

This stack uses **MinIO** (S3-compatible storage), **Apache Iceberg** (table format), and **Dremio** (query engine) as the data warehouse. **dbt** runs against Dremio to build:

| Layer | Source | Materialization |
|-------|--------|-----------------|
| **Landing** | Parquet files (MinIO `mysql_to_landing`) | Source only |
| **Bronze** | Landing → stg + transformations | Iceberg table |
| **Silver** | Bronze → data warehouse (dw) | Iceberg table |
| **Gold** | Silver → data marts (dm) | Iceberg table |

**No Postgres** required; Airflow uses SQLite for metadata, Metabase uses H2.

## Architecture

- **MinIO**: Object storage (S3 API). Holds Iceberg table data and metadata.
- **Apache Iceberg**: Table format (ACID, schema evolution, partitioning).
- **Dremio**: Query engine; connects to MinIO, queries Iceberg tables, exposes SQL/ODBC/JDBC.
- **dbt**: Uses **dbt-dremio** adapter; runs `dbt run` / `dbt test` against Dremio.
- **Airflow**: SQLite for metadata; orchestrates ingestion (MySQL → Iceberg) and dbt (Dremio target).
- **Metabase**: H2 for its app DB; connect to Dremio for BI.

## Quick start

1. **Start the stack** (no Postgres):

   ```bash
   docker compose up -d
   ```

2. **MinIO**: Console at http://localhost:9001 (minioadmin / minioadmin). Create a bucket, e.g. `warehouse`.

3. **Dremio**: Web UI at http://localhost:9047. First-run: create admin user.
   - Add **MinIO as S3 source** (required for dbt CREATE TABLE / Iceberg):
     - Add Source → **Amazon S3** (under Object Storage)
     - AWS Access Key / Secret: MinIO credentials (e.g. minioadmin / minioadmin)
     - **Advanced Options**:
       - ✓ **Enable compatibility mode** (required for MinIO)
       - **Connection Properties**:
         - `fs.s3a.path.style.access` = `true`
         - `fs.s3a.endpoint` = `minio:9000` (no `http://`, or use `host.docker.internal:9000` from host)
       - **Default CTAS Format** = **ICEBERG** (required for dbt tables)
       - **Allowlisted buckets**: `landing`, `raw` (or your buckets)
     - Name the source `minio` (or set `DREMIO_OBJECT_STORAGE_SOURCE` to match)
   - If you get *"You cannot create a table in a space"*: MinIO must be added as **Amazon S3** (Object Storage), not as NAS/file. Set **Default CTAS Format** to **ICEBERG**.
   - If you get *"Object 'landing' not found within 'minio'"*: Create the `landing` bucket in MinIO (Console or `./scripts/deploy.sh datalake`), add `landing` to the MinIO source **Allowlisted buckets** in Dremio, and run the **mysql_to_landing** DAG to populate data.

4. **Ingest MySQL → Iceberg**: See [Ingestion](#ingestion-mysql--iceberg) below.

5. **Run dbt against Dremio**:

   ```bash
   # From host (if dbt-dremio installed)
   export DREMIO_HOST=localhost DREMIO_USER=dremio DREMIO_PASSWORD=dremio
   dbt run --target dremio_dev --project-dir dbt --profiles-dir dbt

   # Or via script
   DREMIO_HOST=localhost ./scripts/dbt/run_lakehouse.sh
   ```

   From Airflow (scheduler has dbt-dremio): use the **data_pipeline_lakehouse** DAG (runs dbt with Dremio target).

## dbt profile (Dremio)

In `dbt/profiles.yml` the targets `dremio_dev` and `dremio_prod` use env vars:

| Env var | Default | Description |
|--------|---------|-------------|
| DREMIO_HOST | localhost | Dremio coordinator host |
| DREMIO_PORT | 9047 | Dremio port |
| DREMIO_USER | dremio | Username |
| DREMIO_PASSWORD | dremio | Password |
| DREMIO_OBJECT_STORAGE_SOURCE | minio | Name of S3/MinIO source in Dremio |
| DREMIO_OBJECT_STORAGE_PATH | no_schema | Path in that source (no_schema = flat bronze/silver/gold) |
| DREMIO_SPACE | dbt | Dremio space for dbt-created objects |
| DREMIO_SPACE_FOLDER | public | Folder in that space |

When Airflow runs in Docker, set `DREMIO_HOST=dremio`.

## Ingestion: MySQL → Landing (Parquet)

The **mysql_to_landing** DAG reads from MySQL and writes Parquet files to the MinIO `landing` bucket:

- **Path:** `s3://landing/{schema}/{table}/data.parquet` (e.g. `landing/mimdbuat01/plants/data.parquet`)
- **Tables:** plants, licenses (configurable)
- Add **mysql_source** connection in Airflow. Ensure the `landing` bucket exists (run `./scripts/deploy.sh datalake` or Terraform).

**Dremio**: Add MinIO as S3 source, then create physical datasets for `landing.mimdbuat01.plants`, `landing.mimdbuat01.licenses` (or configure `LANDING_SCHEMA` env var in dbt to match your Dremio path).

## Ingestion: Landing → Iceberg (optional)

Raw Parquet in landing can be promoted to **Iceberg** for Dremio querying.

### Option A: Spark + Iceberg (recommended for automation)

Use Apache Spark with the Iceberg Spark runtime to read from MySQL (JDBC) and write Iceberg tables to MinIO.

1. Run a Spark job (e.g. in a Spark container or on a cluster) that:
   - Reads `mimdbuat01.plants`, `licenses` via JDBC.
   - Writes to an Iceberg catalog pointing at MinIO (REST catalog or Hadoop catalog with S3).

2. Example (high level): use `org.apache.iceberg:iceberg-spark-runtime` and S3/MinIO config; create Iceberg tables in a bucket/path that Dremio will use as a source.

3. Airflow can trigger this job via `SparkSubmitOperator` or a BashOperator that runs `spark-submit` in a Spark container. See `scripts/lakehouse/` for a sample Spark job (if added).

### Option B: Dremio

- Add **MySQL** as a source in Dremio (your `mysql_source` connection).
- Add **MinIO/S3** as a source and enable Iceberg.
- In Dremio SQL, create Iceberg tables and load data, e.g.:
  - Create table in MinIO (Iceberg) and `INSERT INTO iceberg_table SELECT * FROM mysql_source.mimdbuat01.plants` (syntax depends on Dremio version).

### Option C: Airbyte / Kafka Connect

Use [Airbyte](https://www.dremio.com/blog/how-to-create-a-lakehouse-with-airbyte-s3-apache-iceberg-and-dremio/) or Kafka Connect to sync MySQL → S3/Iceberg; then point Dremio at the same bucket/path.

## Airflow

- **Connections**: Keep `mysql_source` for MySQL → landing. No Postgres warehouse connection.
- **DAGs**:
  - **mysql_to_landing**: MySQL → MinIO Parquet (plants, licenses).
  - **data_pipeline_lakehouse**: dbt against Dremio (`--target dremio_dev`).
  - **test_connections**: Verify MySQL and Dremio connectivity.

## Summary

| Component | Lakehouse stack |
|----------|-----------------|
| Storage | MinIO (S3) |
| Table format | Apache Iceberg |
| Query engine | Dremio |
| dbt adapter | dbt-dremio |
| dbt target | dremio_dev / dremio_prod |
| Ingestion | mysql_to_landing DAG (MySQL → Parquet) → dbt (landing → bronze → silver → gold) |
