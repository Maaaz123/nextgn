-- Gold (dm): business mart – plant counts by state/date
{{ config(schema="gold", materialized="table") }}

with dw as (
  select * from {{ ref("dw_dim_plants") }}
),

summary as (
  select
    state,
    created_date,
    count(*) as plant_count
  from dw
  group by 1, 2
)

select * from summary order by created_date desc, state
