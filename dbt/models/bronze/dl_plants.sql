-- Bronze (dl): raw copy of plants
{{ config(schema="bronze", materialized="view") }}

select * from {{ source("raw", "plants") }}
