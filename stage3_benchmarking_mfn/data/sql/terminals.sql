SELECT DISTINCT terminalname
FROM "APMT-BEATS"."Global"."insights_and_visualizations"."Vessel Moves Insights - Power BI"."GBL_service_list"
WHERE terminalname IS NOT NULL AND terminalname <> ''
ORDER BY terminalname
