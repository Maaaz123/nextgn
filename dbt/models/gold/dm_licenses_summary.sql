-- Gold (dm): business mart – license counts by type/date
{{ config(schema="gold", materialized="table") }}

with dw as (
  select * from {{ ref("dw_dim_licenses") }}
),

summary as (
  select
    license_type,
    created_date,
    count(*) as license_count,
    count(distinct user_id) as unique_users
  from dw
  group by 1, 2
)

select * from summary order by created_date desc, license_type
