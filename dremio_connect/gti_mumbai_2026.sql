SELECT
  "Year",
  "Quarter",
  "Month",
  SUM(total_revenue)                                   AS total_revenue,
  SUM(total_moves)                                     AS total_moves,
  CASE WHEN SUM(total_moves) <> 0
       THEN SUM(total_revenue) / SUM(total_moves) END  AS revenue_per_move
FROM "APMT-BEATS"."Global"."insights_and_visualizations"."MINS"."OneStream"."OS_T"
WHERE Terminal_SalesForce = 'Mumbai (GTI)'
  AND "Year" = '2026'
GROUP BY "Year", "Quarter", "Month"
ORDER BY "Month"
