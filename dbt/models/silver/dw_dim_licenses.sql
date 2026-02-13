-- Silver (dw): dimension table – license entity for analytics
{{ config(schema="silver", materialized="view") }}

select * from {{ ref("stg_licenses") }}
