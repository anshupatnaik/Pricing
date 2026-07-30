SELECT
  "Year",
  "Month",
  SUM(total_revenue) AS total_revenue,
  SUM(total_moves)   AS total_moves
FROM "APMT-BEATS"."Global"."insights_and_visualizations"."MINS"."OneStream"."OS_T"
WHERE Terminal_SalesForce = 'Mumbai (GTI)'
  AND "Year" IN ('2025', '2026')
GROUP BY "Year", "Month"
ORDER BY "Month", "Year"
