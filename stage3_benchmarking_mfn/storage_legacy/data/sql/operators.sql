SELECT DISTINCT container_operator
FROM "APMT-BEATS"."Global"."insights_and_visualizations"."Storage Insights - Power BI"."GBL_Storage_Excel_Simulator"
WHERE container_operator IS NOT NULL AND container_operator <> ''
  AND terminalname = 'GTI Mumbai'
ORDER BY container_operator
