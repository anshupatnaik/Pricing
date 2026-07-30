---
name: pricing-rate-pull
description: How the Stage-3 SL revenue simulator pulls CURRENT quayside rates from the pricing system (BEM benchmarking) and matches them to TOS moves. Use when auto-filling current rates, choosing a rate sheet, or debugging terminal/customer/SKU matching.
---

# Pulling current rates from the pricing system

Volume comes from TOS (`GBL_moves_simulator`, Stage 0); **current rates come from
`Pricing Automation Workflow.Benchmarking.BEM_Pricing_Base`** (Stage 3, "BEM"). Logic lives in
`engine/pricing.py`; the fetch/standardization in `data/repository.py` + `data/crosswalk.py`.

## Standardize ALL sources through the Lookups (UPPER(TRIM()) joins)
Every source (moves, shiftings, BEM pricing, Cost_OS) is joined to the RM Lookups so terminal and
customer names line up (for the future CIE platform). Always join with
`UPPER(TRIM(src_col)) = UPPER(TRIM(lookup_col))`.
- `Lookups.Terminal_mapping` columns are **`Raw_Terminal`, `Std_Terminal`** (renamed from
  terminalName/Standard_Terminal — the schema changes; verify before relying on names).
- `Lookups.Customer_mapping` columns: `Operator`, `Standard_Operator_Code`, `Standard_Operator_Name`.

## The chain
1. **Terminal**: TOS terminal → `Std_Terminal` via `Terminal_mapping` (UPPER/TRIM). Override
   `Vado2 → "Vado Gateway Terminal (APM Terminals)"` for BEM/Cost (lookup maps Vado2→itself).
   **Volume sources (moves, shiftings) filter on the raw selected terminal**; BEM/Cost use Std_Terminal.
2. **Customer/Operator**: BEM.Customer now holds legal names (`Maersk Line`, `Hapag-Lloyd AG`, …)
   that map via `Customer_mapping` → `Standard_Operator_Code`. Resolve the picked TOS operator to its
   standard code and join BEM.Customer through `Customer_mapping`. The app lists the standard
   operators available at the terminal and auto-suggests from the sidebar operator.
3. **Activities**: only the quay load/discharge move family (`crosswalk.QUAY_INCLUDE_ACTIVITIES`);
   no global-catalogue comparison.
4. **Rate sheet choice**: keep rows effective today (Start ≤ today ≤ End); if HQ **and** local are
   both effective, pick the **latest contract start date**; if start **and** end are identical →
   **ambiguous**: ask the manager to pick, or upload an Excel/CSV.
5. **SKU match**: TOS `key` (`Full-Discharge-20`) → BEM `SKU`
   (`activity_ContainerLength_Direction_FreightType_ContainerType`). Prefer exact freight+length,
   else the blended (`Any`) rate. Only **20/40/45 ft** (others excluded); `STRGE` excluded.

## OOG & overtime surcharges (applied "on top of" a base activity)
Two extra BEM tables under `…Benchmarking`, pulled alongside the base rates in the detailed-mode
"Pull current rates" button (`repository.get_oog_surcharge` / `get_overtime_rates`, logic in
`engine/pricing.py`). **Both are expressed as a percentage of the referenced base rate _or_ a fixed
amount** (`engine.pricing.parse_rate` handles `'200.00%'`, `'1029'`+`fixed`, and `NA`/`On Request`→
skip). They are added on top of the base move (which is already counted), so the surcharge line
carries only the surcharge amount.
- **`BEM_Pricing_Surcharge`** — OOG line uses `Surcharge_name='OOG - Standard or Over height Spreader'`
  priced against the **Load or Discharge Move** activity (rate-sheet §2.1); amount = base L/D rate ×
  pct (or the fixed value). `engine.pricing.oog_surcharge`.
- **`BEM_Pricing_Overtime`** — a **day/time-banded** percentage (e.g. Mon–Fri 00:00–07:00 = 75%,
  Sun = 90%) applied on top of quay ops (§2). Match a bucket (`Monday - 03:00-03:59`) by activity
  (prefer L/D) + `Surcharge_overtime_startDay/endDay` + `startTime/endTime` (**both bands may wrap**
  midnight / the week). Only Quay/Vessel-Operations categories are eligible — **never Gate**
  (§4). `engine.pricing.overtime_rate`. Effective-sheet pick reuses `choose_rate_sheet`.
- The representative base L/D rate is `_representative_ld_rate` in the app (Full L/D 40ft preferred).
- Terminals with no BEM surcharge/overtime rows (e.g. Port Elizabeth) → these fall back to manual
  entry, exactly like the base quay rates.

## Rate basis (per move vs per cycle)
BEM rate = **per single move (half cycle)**; TOS volume = **per single move** → revenue = rate ×
moves (no ÷2). Some pricing is quoted **per 2 moves (full cycle)** — mainly Transshipment/Restow.
`engine.pricing.apply_basis` halves the rate when an activity is set to `per_cycle`; default `per_move`.

## Ask the pricing manager
- Which **pricing customer** (BEM) to use when the auto-suggestion is wrong or missing.
- On an **ambiguous** rate sheet (same dates), which sheet — or upload the correct one.
- For **Transshipment/Restow**, whether that rate is per single move or per full cycle.
- Terminals with **no BEM rates** (e.g. GTI Mumbai, Aqaba, Salala) → rates via upload/manual.
