# dbt tests & data quality

- **Schema tests** (in `models/*/schema.yml`): `unique`, `not_null` on primary keys and critical columns for bronze, silver, gold.
- **Source tests** (in `models/sources.yml`): `not_null` on landing `id` and `updated_at` for plants, licenses.
- **Singular tests**: Add SQL that returns rows = failure (e.g. `no_future_dates_*`, `no_negative_counts_*`).

Run all tests: `dbt test`  
Run only singular tests: `dbt test --select test_type:singular`
