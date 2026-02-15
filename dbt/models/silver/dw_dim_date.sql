-- Silver (dw): dimension table – date dimension for analytics (join on created_date, etc.)
-- Dremio-compatible: no :: casts, no generate_series; uses cross-join number spine
{{ config(schema="silver", materialized="table") }}

WITH digits AS (
  SELECT 0 AS d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
  UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9
),
numbers AS (
  SELECT (a.d + b.d * 10 + c.d * 100 + d.d * 1000) AS n
  FROM digits a, digits b, digits c, digits d
  WHERE (a.d + b.d * 10 + c.d * 100 + d.d * 1000) <= 8000
),
date_spine AS (
  SELECT DATE_ADD(CAST('{{ var("dim_date_start") }}' AS DATE), n) AS date_date
  FROM numbers
  WHERE DATE_ADD(CAST('{{ var("dim_date_start") }}' AS DATE), n) <= CAST('{{ var("dim_date_end") }}' AS DATE)
),
enriched AS (
  SELECT
    CAST(TO_CHAR(date_date, 'yyyyMMdd') AS INTEGER) AS date_key,
    date_date,
    EXTRACT(DAY FROM date_date) AS day_of_month,
    EXTRACT(DOW FROM date_date) AS day_of_week,
    TO_CHAR(date_date, 'Dy') AS day_name_short,
    TO_CHAR(date_date, 'Day') AS day_name_long,
    EXTRACT(WEEK FROM date_date) AS week_of_year,
    EXTRACT(MONTH FROM date_date) AS month_num,
    TO_CHAR(date_date, 'Mon') AS month_name_short,
    TO_CHAR(date_date, 'Month') AS month_name_long,
    EXTRACT(QUARTER FROM date_date) AS quarter,
    EXTRACT(YEAR FROM date_date) AS year_num,
    (date_date = CAST(DATE_TRUNC('week', date_date) AS DATE)) AS is_week_start,
    EXTRACT(DOW FROM date_date) IN (0, 6) AS is_weekend,
    TO_CHAR(date_date, 'yyyy-MM') AS year_month
  FROM date_spine
)
SELECT * FROM enriched ORDER BY date_date
