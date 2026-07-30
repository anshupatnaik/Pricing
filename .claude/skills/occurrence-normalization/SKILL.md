---
name: occurrence-normalization
description: How vessel-move occurrences are derived from Dremio and normalized (current-period vs annualized vs move-normalized) in the Stage-3 SL revenue simulator. Use when fetching moves, deriving occurrences, choosing the occurrence basis, or computing RPM denominators.
---

# Occurrence normalization

Occurrences are the billable counts that rates multiply. They come from `GBL_moves_simulator`
aggregated by the key `UNIT_FREIGHT_GROUP-event_type-cont_length` (e.g. `Full-Load-40`), summing
`total_moves` (see `engine/occurrences.py`). Hazardous-surcharge occurrences combine
`imo_indicator` + rounded `cargo_imdg_types`.

## Extra occurrence types (vUSA PMS: Truck / Rail / OOG / Overtime)
Built in `data/repository.py:get_occurrences` (SQL in `data/queries.py`), matching the workbook's
`Automatic Ocurrences` sheet:
- **Truck Moves / Rail Moves** — gate legs by carrier mode. The workbook rule is **XOR**, not OR:
  a move counts as Truck when **exactly one** of `ACTUAL_IB/OB_VISIT_CARRIER_MODE` = `TRUCK`
  (`SUMIFS(J=TRUCK,K<>TRUCK)+SUMIFS(J<>TRUCK,K=TRUCK)`), and Rail likewise for `TRAIN`. A both-legs
  row is excluded; a truck↔rail intermodal container counts once in **each** group. Items are
  `Truck-Full-40`, `Rail-Empty-20`, … (`sql_gate_leg_occurrences`, `engine.occurrences.gate_key`).
- **OOG** — a single line `OOG with spreader or slings` = `SUM(total_moves)` where
  `oog_indicator='OOG'` (not per length). `sql_oog_occurrences`, `engine.occurrences.OOG_ITEM`.
- **Overtime Vessel Moves** — one line per day-hour bucket, keyed verbatim by the moves column
  `overtime_inidcator` (**note the source typo**), e.g. `Monday - 00:00-00:59`.
  `sql_overtime_occurrences`.
- Truck/Rail/OOG/Overtime are all `vessel_move=False` (landside/surcharge lines, excluded from the
  RPM denominator). Validated live vs the Port Elizabeth/2025 vUSA workbook to <1% (snapshot drift).

## Basis options (workbook `Input Filters!F20`)
- **Current period** — occurrences exactly as they occurred in the selected date range.
- **Annualized** — `count × 365 / days_in_range` (`engine.occurrences.annualize`). Use when the
  range is a partial year but the deal is annual.
- **Move-normalized** — scale so total vessel moves equal a manager-supplied target (for
  what-if volumes). Applies proportionally across items.

RPM (revenue per move) uses **total vessel moves** = sum of occurrences flagged `vessel_move`
(hazardous surcharges are excluded from the denominator).

## Ask the pricing manager
- Which basis: current, annualized, or a specific target move count?
- If move-normalized: the target annual moves (and/or vessel calls).
- Whether to include hazardous-surcharge occurrences.
