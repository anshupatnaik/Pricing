---
name: rebate-emptypool-storage
description: Rebate, empty-pool, storage and surcharge assumptions in the Stage-3 SL revenue simulator simple (Hapag) mode. Use when entering rebates, empty-pool terms, storage totals, or OOG/IMO surcharges in share-based simulations.
---

# Rebate, empty pool, storage & surcharges (simple mode)

From the Hapag "Vado HMM (2)" build-up (`engine/simple_model.py`):

    rebate              = rebate_rate × full_LD_share × volume        (subtracted)
    total_after_rebate  = total − rebate
    imo/oog surcharge   = volume × share × surcharge_mult × full_LD_rate
    overtime            = quay_revenue × overtime_pct
    total_revenue       = total_after_rebate + storage + empty_pool   (storage/empty are pasted totals)

## Rules / assumptions
- **Rebate** is a per-full-move rate applied to the full-L/D share of volume (validated to the
  cent against the workbook). Rebates are usually **conditional** (e.g. "≥140k GW moves") — record
  the condition alongside the value; the tool does not auto-enforce conditions.
- **OOG/IMO surcharges** are multipliers on the full-L/D rate (defaults: OOG 1.0, IMO 0.5).
- **Storage & empty-pool** revenue are entered as pasted totals per scenario (not derived from
  rates in this model); keep them optional and clearly separated from quay/gate revenue.

## Ask the pricing manager
- Rebate rate per scenario **and its condition** (volume threshold, cargo type).
- OOG/IMO surcharge multipliers if they differ from defaults.
- Storage totals and empty-pool terms (free TEU/day, rate thereafter) per scenario, if in scope.
