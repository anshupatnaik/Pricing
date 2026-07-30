---
name: overtime-assumptions
description: How overtime is modelled in the Stage-3 SL revenue simulator (average uplift % vs detailed hourly weekday/weekend grid) and applied to quay revenue. Use when a pricing manager enters or reviews overtime, or when reproducing the Hapag Overtime tab.
---

# Overtime assumptions

Overtime adds revenue on top of quay/vessel-move revenue. In the simple (Hapag) model:

    overtime_revenue[scenario] = quay_revenue[scenario] × overtime_pct[scenario]

## Two input paths (both yield one uplift % per scenario)
- **Average uplift %** (default) — the manager types a single % per scenario. This is the direct,
  fast path and matches `Overtime!D170`-style averages in the workbook.
- **Detailed hourly grid** (optional) — per-hour weekday/weekend overtime factors per operator
  (the `Overtime` tab). `engine.overtime.average_uplift` / `uplift_from_grid` average the grid
  down to the per-scenario %.

## Rules / assumptions
- Overtime applies to **quay revenue only** (load/discharge, transhipment, shift), not gate,
  storage, or surcharges.
- If a manager has real overtime data from prior periods, prefer entering it as the hourly grid
  and let the tool average it, so the assumption is transparent.

## Ask the pricing manager
- Average overtime % per scenario, OR their hourly weekday/weekend overtime data.
- Whether overtime should apply beyond quay revenue (default: no).
