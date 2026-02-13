-- Data quality: gold marts must not have negative counts (fails if any exist)
select 1 as dq_fail
where exists (select 1 from {{ ref("dm_flows_summary") }} where flow_count < 0)
   or exists (select 1 from {{ ref("dm_licenses_summary") }} where license_count < 0)
   or exists (select 1 from {{ ref("dm_plants_summary") }} where plant_count < 0)
