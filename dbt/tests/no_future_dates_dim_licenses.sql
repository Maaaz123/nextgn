-- Data quality: no license records with created_at in the future
select id, created_at, created_date
from {{ ref("dw_dim_licenses") }}
where created_date > current_date
   or (created_at is not null and created_at::date > current_date)
