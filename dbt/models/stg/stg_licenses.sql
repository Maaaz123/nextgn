-- Stg: transformation view – clean licenses from dl
{{ config(schema="staging", materialized="view") }}

with dl as (
  select * from {{ ref("dl_licenses") }}
),

cleaned as (
  select
    id,
    old_id,
    user_id,
    commercial_entity_id,
    investment_type,
    investment_size,
    "number",
    meta,
    license_type,
    expires_at,
    issue_date,
    renewed_at,
    canceled_at,
    cancelled_by,
    investor_id,
    created_at,
    updated_at,
    deleted_at,
    cancelled_by_penalty,
    suspended_at,
    ndb_synched_at,
    ndb_last_ops_at,
    created_at::date as created_date
  from dl
)

select * from cleaned
