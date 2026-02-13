-- Silver (dw): fact table – flow events/records for analytics
{{ config(schema="silver", materialized="view") }}

select * from {{ ref("stg_flows") }}
