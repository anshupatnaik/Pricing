SELECT
  COALESCE(NULLIF(TRIM(Standard_Terminal), ''), Terminal_SalesForce) AS terminal,
  SUM(total_moves)   AS total_moves_2025,
  SUM(total_revenue) AS total_revenue_2025
FROM "APMT-BEATS"."Global"."insights_and_visualizations"."MINS"."OneStream"."OS_T"
WHERE "Year" = '2025'
GROUP BY COALESCE(NULLIF(TRIM(Standard_Terminal), ''), Terminal_SalesForce)
ORDER BY total_moves_2025 DESC
