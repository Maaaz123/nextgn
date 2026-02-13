-- Silver (dw): dimension table – plant entity for analytics
{{ config(schema="silver", materialized="view") }}

select * from {{ ref("stg_plants") }}
