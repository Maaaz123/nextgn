-- Silver (dw): plant profile dimension – plant + license attributes for analytics
{{ config(schema="silver", materialized="table") }}

WITH plants AS (
    SELECT * FROM {{ ref("stg_plants") }}
),
licenses AS (
    SELECT * FROM {{ ref("stg_licenses") }}
)
SELECT
    p.PLANT_KEY,
    p.PLANT_ID,
    p.LICENSE_ID,
    p.ADDRESS_ID,
    p.INDUSTRIAL_CITY_ID,
    p.PLANT_status,
    p.PLANT_NUMBER,
    p.plant_status_ar,
    p.land_provider_ar,
    p.LAND_PROVIDER_en,
    p.IS_RENT,
    p.CLOSED_AT,
    p.CREATED_AT AS PLANT_CREATED_AT,
    p.UPDATED_AT AS PLANT_UPDATED_AT,
    p.CANCELED_AT AS PLANT_CANCELED_AT,
    p.ESTABLISHED_AT,
    p.HS_12_CONFIRMED_AT,
    p.HAS_APPROVED_MANPOWER,
    p.MAIN_ACTIVITY_CODE_L2,
    p.MAIN_ACTIVITY_CODE_L4,
    p.STARTED_PRODUCTION_AT,
    p.INSIDE_INDUSTRIAL_CITY,
    p.GAS_WASTE,
    p.LAND_AREA,
    p.SOLID_WASTE,
    p.STORES_AREA,
    p.LIQUID_WASTE,
    p.PRODUCT_AREA,
    p.BUILDING_AREA,
    p.RENTAL_AMOUNT,
    p.MANAGMENT_AREA,
    p.CONSTRUCTION_COST,
    p.ANNUAL_WORKING_DAYS,
    p.DAILY_WORKING_HOURS,
    p.EXPECTED_LABOR_POWER,
    p.MANUFACTURING_METHOD,
    l.LICENSE_KEY,
    l.USER_ID,
    l.LICENSE_NUMBER,
    l.LICENSE_EXPIRES_AT,
    l.LICENSE_ISSUE_DATE,
    l.LICENSE_RENEWED_AT,
    l.LICENSE_CYCLE,
    l.license_status AS LICENSE_STATUS,
    l.INVESTOR_ID,
    l.INVESTMENT_SIZE,
    l.INVESTMENT_TYPE,
    l.ENTITY_ID,
    l.AREA AS LICENSE_AREA,
    l.CITY AS LICENSE_CITY,
    p.LOAD_DATE
FROM plants p
LEFT JOIN licenses l ON p.LICENSE_ID = l.LICENSE_ID
