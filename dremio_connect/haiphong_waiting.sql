-- Haiphong river vs deep-water terminal waiting-time analysis
-- Source: Container_Cloud.model.final.calls_with_move_count (AIS vessel-call grain, 1 row = 1 terminal call)
-- Scope:  Port = Haiphong, vessel_type_ais = 'Container Ship'
--
-- Definitions
--   Group        : deep-water = Haiphong International Container Terminal (HICT, Lach Huyen, ~11m draft,
--                  ~285m LOA, ~7000 TEU); river = every other Haiphong berth (draft <= 8.7m, feeders).
--   Waiting time : prev_leg_stationary_hours = hours the vessel sat stationary (anchored/drifting) on the
--                  approach leg before berthing. Best AIS proxy for pre-berth waiting. Outlier-prone
--                  (laid-up vessels), so we report MEDIAN and a mean capped at <= 120h.
--   Berth stay   : Duration = arrival_time -> departure_time inside the terminal polygon (hours).
--   Excludes     : Cang Transvina (single laid-up call, 697h outlier).

-- =========================================================================
-- A. Full-year 2025 group summary (river vs deep-water)
-- =========================================================================
SELECT
  CASE WHEN Terminal = 'Haiphong International Container Terminal'
       THEN 'Deep-water (Lach Huyen)' ELSE 'River terminals' END          AS grp,
  COUNT(*)                                                                 AS calls,
  ROUND(AVG(max_draft), 1)                                                 AS avg_draft_m,
  ROUND(AVG(length),   0)                                                  AS avg_loa_m,
  ROUND(AVG(vesteu),   0)                                                  AS avg_teu,
  ROUND(MEDIAN(Duration), 1)                                              AS med_berth_stay_h,
  ROUND(MEDIAN(prev_leg_stationary_hours), 1)                            AS med_wait_h,
  ROUND(AVG(CASE WHEN prev_leg_stationary_hours <= 120
                 THEN prev_leg_stationary_hours END), 1)                  AS capmean_wait_h
FROM "Container_Cloud"."model"."final"."calls_with_move_count"
WHERE Port = 'Haiphong'
  AND vessel_type_ais = 'Container Ship'
  AND Terminal <> 'Cang Transvina'
  AND "year" = 2025
GROUP BY CASE WHEN Terminal = 'Haiphong International Container Terminal'
              THEN 'Deep-water (Lach Huyen)' ELSE 'River terminals' END
ORDER BY grp;

-- =========================================================================
-- B. Q1/Q2 year-on-year: 2026 vs 2025 (run separately from A)
--   NB: use an explicit quarter CASE. "month"/3 does INTEGER division in
--       Dremio and mis-buckets the quarters -- do not use it.
-- =========================================================================
-- SELECT
--   CASE WHEN Terminal = 'Haiphong International Container Terminal'
--        THEN 'Deep-water' ELSE 'River' END                               AS grp,
--   CASE WHEN "month" <= 3 THEN 'Q1' WHEN "month" <= 6 THEN 'Q2' END      AS q,
--   "year"                                                                AS yr,
--   COUNT(*)                                                              AS calls,
--   ROUND(MEDIAN(Duration), 1)                                           AS med_berth_stay_h,
--   ROUND(MEDIAN(prev_leg_stationary_hours), 1)                         AS med_wait_h,
--   ROUND(AVG(CASE WHEN prev_leg_stationary_hours <= 120
--                  THEN prev_leg_stationary_hours END), 1)               AS capmean_wait_h
-- FROM "Container_Cloud"."model"."final"."calls_with_move_count"
-- WHERE Port = 'Haiphong'
--   AND vessel_type_ais = 'Container Ship'
--   AND Terminal <> 'Cang Transvina'
--   AND "year" IN (2025, 2026)
--   AND "month" <= 6
-- GROUP BY 1, 2, 3
-- ORDER BY grp DESC, q, yr;
