SELECT unit_category_fixed, container_length, dwell_days,
       SUM(container_count) AS container_count
FROM "APMT-BEATS"."Global"."insights_and_visualizations"."Storage Insights - Power BI"."GBL_Storage_Excel_Simulator"
WHERE terminalname = 'GTI Mumbai'
  AND month_date >= '2024-01-01'
  AND month_date <= '2024-12-31'
  AND freight_kind = 'Full'
  AND unit_category_fixed <> 'Restow'
  AND unit_requires_power = '1' AND cargo_is_hazardous = '0'
GROUP BY unit_category_fixed, container_length, dwell_days
