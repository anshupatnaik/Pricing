---
name: dremio-moves-sources
description: The Dremio source tables, filters, and data grain behind the Stage-3 SL revenue simulator (GBL_moves_simulator, GBL_service_list, GBL_Shift_on_board_simulator). Use when writing/adjusting SQL, debugging data fetches, or explaining where volume/moves data comes from.
---

# Dremio moves sources

Schema: `"APMT-BEATS"."Global"."insights_and_visualizations"."Vessel Moves Insights - Power BI"`.
Accessed via the repo's existing `dremio_connect.DremioClient` (PAT in `DREMIO_TOKEN`/`.env`).
SQL builders live in `data/queries.py`; the only Dremio-touching code is `data/repository.py`.

| Table | Use | Key filters |
|-------|-----|-------------|
| `GBL_moves_simulator` | occurrence source (vessel moves) | `terminalname`, `event_date` BETWEEN from/to, `event_year > 2017`, `unit_container_operator_id IN (…)` (≤15), `service_name IN (…)` (≤15) |
| `GBL_service_list` | pickers (terminal/operator/service) | distinct `terminalname, unit_container_operator_id, service_name` |
| `GBL_Shift_on_board_simulator` | restow / shift-on-board | filters on `container_operator_id`, `actual_ob_service_name` |

## Grain / caveats
- Occurrence key = `unit_freight_group-event_type-cont_length`; count = `SUM(total_moves)`.
- Operator/service **column names differ** between moves and shiftings tables (see table above) —
  keep the two SQL builders distinct.
- Escape string parameters (`_q`, doubling single quotes). Prefer `--sql-file`/the Python client
  over PowerShell inline SQL (embedded double-quotes get mangled — see `dremio_connect/README.md`).
- To discover valid service names, pull without a service filter first and read `GBL_service_list`.

## Ask the pricing manager
- Terminal, operators, services, and the date range to pull.
- Whether to include shiftings/restow moves.
