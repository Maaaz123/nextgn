-- Gold (dm): plant mart – total plants by year, month, status, land provider, license status
{{ config(schema="gold", materialized="table") }}

SELECT
    EXTRACT(YEAR FROM PLANT_CREATED_AT) AS year_num,
    EXTRACT(MONTH FROM PLANT_CREATED_AT) AS month_num,
    plant_status_ar,
    LAND_PROVIDER_en,
    LICENSE_STATUS,
    COUNT(*) AS total_plant
FROM {{ ref("dw_dim_plant_profile") }}
GROUP BY
    EXTRACT(YEAR FROM PLANT_CREATED_AT),
    EXTRACT(MONTH FROM PLANT_CREATED_AT),
    plant_status_ar,
    LAND_PROVIDER_en,
    LICENSE_STATUS
ORDER BY year_num, month_num, total_plant DESC
