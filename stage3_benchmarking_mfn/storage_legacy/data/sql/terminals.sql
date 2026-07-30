SELECT DISTINCT terminalname
FROM "APMT-BEATS"."Global"."insights_and_visualizations"."Storage Insights - Power BI"."GBL_Storage_Excel_Simulator"
WHERE terminalname IS NOT NULL AND terminalname <> ''
ORDER BY terminalname
