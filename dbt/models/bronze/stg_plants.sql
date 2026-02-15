-- Bronze: stg_plants – transformation from landing → Iceberg table (dedup by updated_at)
{{ config(
    materialized="incremental",
    incremental_strategy="merge",
    unique_key="PLANT_ID"
) }}
WITH deduplicated AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) AS row_num
    FROM "minio"."landing"."mimdbuat01"."plants"."data.parquet"
    {% if is_incremental() %}
    WHERE CAST(updated_at AS TIMESTAMP) > (SELECT COALESCE(MAX(UPDATED_AT), TIMESTAMP '1970-01-01 00:00:00') FROM {{ this }})
    {% endif %}
)
SELECT
    ROW_NUMBER() OVER (ORDER BY id) AS PLANT_KEY,
    id AS PLANT_ID,
    address_id AS ADDRESS_ID,
    industrial_city_id AS INDUSTRIAL_CITY_ID,
    state AS PLANT_status,
    CASE WHEN number IS NULL OR TRIM(CAST(number AS VARCHAR)) = '' THEN NULL ELSE CAST(number AS BIGINT) END AS PLANT_NUMBER,
    CAST(
        CASE
            WHEN state = 'new' THEN 'تحت التأسيس'
            WHEN state = 'established' THEN 'تحت الانشاء'
            WHEN state = 'closed' THEN 'مغلق'
            WHEN state = 'active' THEN 'منتج'
            WHEN state = 'canceled' THEN 'ملغي'
            ELSE NULL
        END AS VARCHAR
    ) AS plant_status_ar,
    CAST(
        CASE land_provider
            WHEN 'RCJY' THEN 'الهيئة الملكية للجبيل وينبع'
            WHEN 'MOMRAH' THEN 'وزارة الشؤون البلدية والقروية والإسكان'
            WHEN 'MODON' THEN 'الهيئة السعودية للمدن الصناعية ومناطق التقنية'
            WHEN 'ECZA' THEN 'هيئة المدن والمناطق الإقتصادية الخاصة'
            WHEN 'MEWA' THEN 'وزارة البيئة والمياه والزراعة'
            WHEN 'GACA' THEN 'الهيئة العامة للطيران المدني'
            WHEN 'MAWANI' THEN 'هيئة الموانئ السعودية'
            WHEN 'UNIVERSITIES' THEN 'الجامعات'
            WHEN 'MIM' THEN 'وزارة الصناعة والثروة المعدنية'
            WHEN 'SAR' THEN 'المؤسسة العامة للخطوط الحديدية'
            WHEN 'ARAMCO' THEN 'أرامكو السعودية'
            WHEN 'NEOM' THEN 'نيوم'
            WHEN 'SPARK' THEN 'مدينة الملك سلمان للطاقة'
            WHEN 'OTHER' THEN 'اخرى'
            ELSE NULL
        END AS VARCHAR
    ) AS land_provider_ar,
    is_rent AS IS_RENT,
    CAST(closed_at AS TIMESTAMP) AS CLOSED_AT,
    CAST(created_at AS TIMESTAMP) AS CREATED_AT,
    license_id AS LICENSE_ID,
    CAST(updated_at AS TIMESTAMP) AS UPDATED_AT,
    CAST(canceled_at AS TIMESTAMP) AS CANCELED_AT,
    land_provider AS LAND_PROVIDER_en,
    CAST(established_at AS TIMESTAMP) AS ESTABLISHED_AT,
    CAST(hs_12_confirmed_at AS TIMESTAMP) AS HS_12_CONFIRMED_AT,
    ndb_synched_at AS NDB_SYNCHED_AT,
    ndb_last_ops_at AS NDB_LAST_OPS_AT,
    has_approved_manpower AS HAS_APPROVED_MANPOWER,
    CASE WHEN main_activity_code_l2 IS NULL OR TRIM(CAST(main_activity_code_l2 AS VARCHAR)) = '' THEN NULL ELSE CAST(main_activity_code_l2 AS INTEGER) END AS MAIN_ACTIVITY_CODE_L2,
    CASE WHEN main_activity_code_l4 IS NULL OR TRIM(CAST(main_activity_code_l4 AS VARCHAR)) = '' THEN NULL ELSE CAST(main_activity_code_l4 AS INTEGER) END AS MAIN_ACTIVITY_CODE_L4,
    CAST(started_production_at AS TIMESTAMP) AS STARTED_PRODUCTION_AT,
    inside_industrial_city AS INSIDE_INDUSTRIAL_CITY,
    -- TODO: Extract from meta JSON when structure verified. Run: SELECT meta FROM "minio"."landing"."mimdbuat01"."plants"."data.parquet" LIMIT 1
    CAST(NULL AS VARCHAR) AS GAS_WASTE,
    CAST(NULL AS DOUBLE) AS LAND_AREA,
    CAST(NULL AS VARCHAR) AS SOLID_WASTE,
    CAST(NULL AS DOUBLE) AS STORES_AREA,
    CAST(NULL AS VARCHAR) AS LIQUID_WASTE,
    CAST(NULL AS DOUBLE) AS PRODUCT_AREA,
    CAST(NULL AS DOUBLE) AS BUILDING_AREA,
    CAST(NULL AS DOUBLE) AS RENTAL_AMOUNT,
    CAST(NULL AS DOUBLE) AS MANAGMENT_AREA,
    CAST(NULL AS DOUBLE) AS CONSTRUCTION_COST,
    CAST(NULL AS INTEGER) AS ANNUAL_WORKING_DAYS,
    CAST(NULL AS INTEGER) AS DAILY_WORKING_HOURS,
    CAST(NULL AS INTEGER) AS EXPECTED_LABOR_POWER,
    CAST(NULL AS VARCHAR) AS MANUFACTURING_METHOD,
    CURRENT_DATE AS LOAD_DATE
FROM deduplicated
WHERE row_num = 1
