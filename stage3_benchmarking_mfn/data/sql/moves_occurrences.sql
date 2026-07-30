SELECT unit_freight_group, event_type, cont_length,
       SUM(total_moves) AS total_moves
FROM "APMT-BEATS"."Global"."insights_and_visualizations"."Vessel Moves Insights - Power BI"."GBL_moves_simulator"
WHERE terminalname = 'GTI Mumbai'
  AND event_date >= '2024-01-01'
  AND event_date <= '2024-12-31'
  AND event_year > 2017
  AND unit_container_operator_id IN ('MAE')
GROUP BY unit_freight_group, event_type, cont_length
