-- Data quality: flow.license_id (when not null) should exist in dw_dim_licenses
-- Fails if any flow references a missing license
select f.id as flow_id, f.license_id
from {{ ref("dw_fact_flows") }} f
left join {{ ref("dw_dim_licenses") }} l on l.id = f.license_id
where f.license_id is not null
  and l.id is null
