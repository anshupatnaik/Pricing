# Reference notes — SL Revenue Simulator (reverse-engineered)

Source workbooks (kept in `stage3_benchmarking_mfn/`, gitignored):
- `Pricing Module Simulator Production version.xlsm` (PMS) — comprehensive, occurrence-based.
- `Hapag simulations Vado 2026-2027.xlsx` — simpler, share-based (tab **Vado HMM (2)**).

## PMS — Dremio sources (schema `"Vessel Moves Insights - Power BI"`)
- `GBL_moves_simulator` — WHERE `terminalname`, `event_date` between From/To, `event_year>2017`,
  `unit_container_operator_id IN (...)` (≤15), `service_name IN (...)` (≤15).
- `GBL_service_list` — `distinct terminalname, unit_container_operator_id, service_name`.
- `GBL_Shift_on_board_simulator` — restow/shift; filters on `container_operator_id`, `actual_ob_service_name`.

### Moves Raw Data columns (GBL_moves_simulator SELECT *)
A Terminalname, B day_of_week, C event_hour, D key_visit, E oog_indicator, F reefer_indicator,
G imo_indicator, H cargo_imdg_types, I SERVICE_NAME, J ACTUAL_OB_VISIT_CARRIER_MODE,
K ACTUAL_IB_VISIT_CARRIER_MODE, L category (Import/Export), M UNIT_FREIGHT_GROUP (Full/Empty),
N event_type (Load/Discharge), O cont_length (20/40/45/53), P UNIT_CONTAINER_OPERATOR_ID,
Q event_date, R event_month, S event_quarter, T event_year, U total_moves,
V overtime_inidcator (`<day> - <hour>`), W key = **`M-N-O`** e.g. `Full-Load-40`.

### Occurrence derivation (Automatic Ocurrences)
`E (occurrences) = SUMIF('Moves Raw Data'.W, item, 'Moves Raw Data'.U)` — i.e. sum of `total_moves`
grouped by the `Full/Empty-Load/Discharge-<length>` key. `Annualized = E*365/(To-From+1)`.
VBA `PopulateUniqueSLRatesAndOccurrences` appends hazardous-surcharge occurrences:
key = `imo_indicator & " " & Int(imdg_types) & " Load/Discharge"`, summing total_moves.

### Revenue chain
- `SL Revenue per Ocurrence`: per item/scenario `= occ × rate ÷ RoE (Input Filters!C37)`; row 39 = totals.
- `Input BCO Revenue`: `occ × BCO rate`; scenario-independent total at `G399`.
- `Result` per scenario: Total Vessel Moves, SL Rev, BCO Rev, Total Rev, Variable Cost
  (`VarCostPerMove(F27, negative) × moves`), Contribution Margin, and per-move metrics.
- Scenario names: `Input Filters!B40:B49` = Current Rates, Scenario 2..8.
- **The shipped PMS file is a clean template (occurrences all 0)** — numeric parity needs live data;
  the revenue math is `occ×rate/RoE`, validated by unit tests + a live DAL smoke test.

## Hapag "Vado HMM (2)" — share-based model (VALIDATED by hand)
- Volume base `B1` (e.g. 100000). Shares: full L/D `B3`, empty L/D `B2`, transhipment `B4`, shift `B5`,
  reefer `B6`, reefer dwell `B7`; gate uses shares `E3=B3`, `E4=B2`; OOG share `E5`, IMO share `E6`.
- Rate columns = scenarios: B Maersk, C Hapag, D HMM Floor (=B+increment), E Maersk+CPI (=B×(1+CPI)),
  F/G/H Hapag Floor/Target/Anchor (=C×(1+factor)), I Closing.
- Revenue build-up (per scenario column, e.g. N=HMM Floor uses D rates):
  - Quay: L/D full `rate×fullShare×vol`, L/D empty, transhipment, shift → **Total Quay** (N6).
  - IMO `vol×imoShare×imdgSurcharge×fullRate`; OOG `vol×oogShare×oogSurcharge×fullRate`.
  - **Overtime = Total Quay × overtime%** (avg from `Overtime!D170…`, ~0.18/0.157/0.214).
  - Gate full/empty `rate×share×vol` → Total Gate (N14). Reefer `rate×(vol×reeferShare)×dwell`.
  - **Total** = Quay+Gate+Reefer+Overtime+IMO+OOG (N18). **Rebate** subtracted → Total w/ rebate (N21).
  - **RPM = total ÷ volume** (N22). Storage lines (Import/Export/Tshpt/OOG/IMO) are pasted totals →
    Total w/ rebate+storage (N33), RPM (N34). Empty-pool revenue optional add-on.
- Parity anchors: N6=8,661,500; N14=1,704,500; N18≈12,279,270; N21≈12,154,270; N22≈121.54;
  N33≈14,632,602; N34≈146.33. (L=Maersk, M=Hapag, N=HMM Floor.)

## Overtime tab
Hourly weekday/weekend overtime % per operator; averaged at row 170 (D=Maersk 0.1798, E=Hapag 0.1571,
F=CMA 0.2143, G=HMM Floor …). Feeds the overtime uplift %.
