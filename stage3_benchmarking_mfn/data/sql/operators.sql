SELECT DISTINCT unit_container_operator_id
FROM "APMT-BEATS"."Global"."insights_and_visualizations"."Vessel Moves Insights - Power BI"."GBL_service_list"
WHERE unit_container_operator_id IS NOT NULL AND unit_container_operator_id <> ''
  AND terminalname = 'GTI Mumbai'
ORDER BY unit_container_operator_id
