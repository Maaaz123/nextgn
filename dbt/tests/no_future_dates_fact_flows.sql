-- Data quality: no flow records with created_at or updated_at in the future
-- Fails if any row is returned
select id, created_at, updated_at
from {{ ref("dw_fact_flows") }}
where created_at::date > current_date
   or updated_at::date > current_date
