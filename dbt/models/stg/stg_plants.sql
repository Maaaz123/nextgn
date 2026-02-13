-- Stg: transformation view – clean plants from dl
{{ config(schema="staging", materialized="view") }}

with dl as (
  select * from {{ ref("dl_plants") }}
),

cleaned as (
  select
    id,
    old_id,
    license_id,
    address_id,
    industrial_city_id,
    land_provider,
    state,
    "number",
    main_activity_code_l2,
    main_activity_code_l4,
    is_rent,
    has_approved_manpower,
    inside_industrial_city,
    started_production_at,
    closed_at,
    established_at,
    canceled_at,
    crm_account_id,
    hs_12_confirmed_at,
    meta,
    created_at,
    updated_at,
    ndb_synched_at,
    ndb_last_ops_at,
    created_at::date as created_date
  from dl
)

select * from cleaned
