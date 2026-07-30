SELECT DISTINCT service_name
FROM "APMT-BEATS"."Global"."insights_and_visualizations"."Vessel Moves Insights - Power BI"."GBL_service_list"
WHERE service_name IS NOT NULL AND service_name <> ''
  AND terminalname = 'GTI Mumbai'
ORDER BY service_name
