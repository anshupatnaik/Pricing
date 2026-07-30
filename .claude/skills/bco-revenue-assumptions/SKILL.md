---
name: bco-revenue-assumptions
description: How BCO (beneficial cargo owner) revenue is added in the Stage-3 SL revenue simulator and why it is scenario-independent. Use when entering BCO rates or including/excluding BCO in the Result.
---

# BCO revenue assumptions (detailed mode)

BCO revenue is charged to cargo owners and added to SL revenue in the `Result`:

    bco_revenue = Σ (occurrences × BCO rate per item)          # engine.revenue.bco_revenue
    total_revenue = SL revenue (scenario) + BCO revenue

## Rules / assumptions
- BCO revenue is **scenario-independent** in the workbook (`Input BCO Revenue!G399` reused across
  all `Result` columns) — it does not change with the SL rate scenario. So the same BCO total is
  added to every scenario.
- BCO rates are per occurrence/item (workbook default 400 per item in the template).
- BCO can be toggled off (SL-only view) via the `include_bco` flag.

## Ask the pricing manager
- BCO rate per item (or a flat per-move BCO rate), if BCO is in scope.
- Whether BCO revenue should be included in this simulation at all.
