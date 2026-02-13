# dbt tests & data quality

- **Schema tests** (in `models/schema.yml`): `unique`, `not_null` on primary keys and critical columns for all layers.
- **Source tests** (in `models/sources.yml`): `not_null` on raw `id` and `updated_at` for flows, plants, licenses.
- **Singular tests** (this folder): SQL that returns rows = failure.
  - `no_future_dates_*`: no created_at/created_date in the future.
  - `no_negative_counts_gold`: gold marts must not have negative counts.
  - `fact_flows_license_id_in_dim`: referential check – flow.license_id exists in dw_dim_licenses when not null.

Run all tests: `dbt test`  
Run only data quality (singular) tests: `dbt test --select test_type:singular`
