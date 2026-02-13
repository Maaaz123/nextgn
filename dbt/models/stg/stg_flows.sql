-- Stg: transformation view – clean and standardize flows from dl
{{ config(schema="staging", materialized="view") }}

with dl as (
  select * from {{ ref("dl_flows") }}
),

cleaned as (
  select
    id,
    old_id,
    user_id,
    assignee_id,
    license_id,
    "number",
    cr_number,
    workflow,
    state,
    status,
    meta,
    finished_at,
    created_at,
    updated_at,
    stage,
    ndb_synched_at,
    ndb_last_ops_at,
    created_at::date as created_date,
    updated_at::date as updated_date
  from dl
)

select * from cleaned
