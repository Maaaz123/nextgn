-- Bronze (dl): raw copy of flows from data lake / raw
{{ config(schema="bronze", materialized="view") }}

select * from {{ source("raw", "flows") }}
