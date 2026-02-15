-- Bronze: stg_licenses – transformation from landing → Iceberg table (dedup by updated_at)
{{ config(
    materialized="incremental",
    incremental_strategy="merge",
    unique_key="LICENSE_ID"
) }}
WITH deduplicated AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) AS row_num
    FROM "minio"."landing"."mimdbuat01"."licenses"."data.parquet"
    {% if is_incremental() %}
    WHERE CAST(updated_at AS TIMESTAMP) > (SELECT COALESCE(MAX(UPDATED_AT), TIMESTAMP '1970-01-01 00:00:00') FROM {{ this }})
    {% endif %}
)
SELECT
    ROW_NUMBER() OVER (ORDER BY id) AS LICENSE_KEY,
    id AS LICENSE_ID,
    user_id AS USER_ID,
    CAST(NULLIF(number, '') AS BIGINT) AS LICENSE_NUMBER,
    CAST(created_at AS TIMESTAMP) AS CREATED_AT,
    CAST(created_at AS DATE) AS created_date,
    CAST(deleted_at AS TIMESTAMP) AS DELETED_AT,
    CAST(expires_at AS TIMESTAMP) AS LICENSE_EXPIRES_AT,
    CAST(issue_date AS TIMESTAMP) AS LICENSE_ISSUE_DATE,
    CAST(renewed_at AS TIMESTAMP) AS LICENSE_RENEWED_AT,
    CAST(updated_at AS TIMESTAMP) AS UPDATED_AT,
    CAST(canceled_at AS TIMESTAMP) AS LICENSE_CANCELED_AT,
    CASE
    WHEN deleted_at IS NOT NULL THEN 'Deleted'
    WHEN canceled_at IS NOT NULL THEN 'Canceled'
    WHEN suspended_at IS NOT NULL THEN 'Suspended'
    WHEN expires_at IS NOT NULL AND CAST(expires_at AS DATE) < CURRENT_DATE THEN 'Expired'
    WHEN issue_date IS NOT NULL AND expires_at IS NOT NULL AND CAST(expires_at AS DATE) >= CURRENT_DATE THEN 'Active'
    ELSE 'Unknown'
    END AS LICENSE_CYCLE,
    CASE
    WHEN CAST(expires_at AS DATE) >= CURRENT_DATE THEN 'Active'
    ELSE 'Expired'
    END AS license_status,
    investor_id AS INVESTOR_ID,
    cancelled_by AS CANCELLED_BY,
    CAST(suspended_at AS TIMESTAMP) AS SUSPENDED_AT,
    investment_size AS INVESTMENT_SIZE,
    investment_type AS INVESTMENT_TYPE,
    commercial_entity_id AS ENTITY_ID,
    -- TODO: Extract from meta JSON when structure verified. Run: SELECT meta FROM "minio"."landing"."mimdbuat01"."licenses"."data.parquet" LIMIT 1
    CAST(NULL AS VARCHAR) AS AREA,
    CAST(NULL AS VARCHAR) AS CITY,
    CAST(NULL AS VARCHAR) AS ENERGY_SOURCE,
    CAST(NULL AS DOUBLE) AS CURRENT_ASSETS,
    CAST(NULL AS BOOLEAN) AS HAS_OTHER_SOURCES,
    CAST(NULL AS DOUBLE) AS NON_CURRENT_ASSETS,
    CAST(NULL AS DOUBLE) AS EXPECTED_LOAN_AMOUNT,
    CAST(NULL AS DOUBLE) AS ELECTRIC_SERVICE_NUMBER,
    CAST(NULL AS BOOLEAN) AS HAS_ELECTRICAL_INFORMATION,
    CAST(NULL AS DOUBLE) AS EXPECTED_FINANCING_FROM_FUNDS_BANKS,
    CAST(NULL AS DOUBLE) AS EXPECTED_FINANCING_FROM_OTHER_SOURCES,
    CAST(NULL AS DOUBLE) AS EXPECTED_FINANCING_FROM_INDUSTRIAL_FUND,
    CAST(NULL AS VARCHAR) AS ANNUAL_EXPECTED_ELECTRICAL_ENERGY_VOLUME,
    CURRENT_DATE AS LOAD_DATE
FROM deduplicated
WHERE row_num = 1
