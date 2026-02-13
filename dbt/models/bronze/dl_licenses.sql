-- Bronze (dl): raw copy of licenses
{{ config(schema="bronze", materialized="view") }}

select * from {{ source("raw", "licenses") }}
