-- Gold (dm): business mart – flow counts by workflow/state/date
{{ config(schema="gold", materialized="table") }}

with dw as (
  select * from {{ ref("dw_fact_flows") }}
),

summary as (
  select
    workflow,
    state,
    created_date,
    count(*) as flow_count,
    count(distinct user_id) as unique_users
  from dw
  group by 1, 2, 3
)

select * from summary order by created_date desc, workflow, state
