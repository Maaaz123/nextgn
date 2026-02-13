-- Silver (dw): dimension table – date dimension for analytics (join on created_date, etc.)
{{ config(schema="silver", materialized="table") }}

with date_spine as (
  select generate_series(
    '{{ var("dim_date_start") }}'::date,
    '{{ var("dim_date_end") }}'::date,
    '1 day'::interval
  )::date as date_date
),

enriched as (
  select
    to_char(date_date, 'YYYYMMDD')::int as date_key,
    date_date,
    extract(day from date_date) as day_of_month,
    extract(dow from date_date) as day_of_week,
    to_char(date_date, 'Dy') as day_name_short,
    to_char(date_date, 'Day') as day_name_long,
    extract(week from date_date) as week_of_year,
    extract(month from date_date) as month_num,
    to_char(date_date, 'Mon') as month_name_short,
    to_char(date_date, 'Month') as month_name_long,
    extract(quarter from date_date) as quarter,
    extract(year from date_date) as year,
    date_date::date = date_trunc('week', date_date)::date as is_week_start,
    extract(dow from date_date) in (0, 6) as is_weekend,
    to_char(date_date, 'YYYY-MM') as year_month
  from date_spine
)

select * from enriched order by date_date
