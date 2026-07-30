---
name: deal-tracker-cpi
description: How closed deals are recorded and compared to CPI (at/above/below CPI) with revenue upside in the Stage-3 SL revenue simulator Deal Tracker. Use when saving a simulation as a closed deal, choosing the closed scenario, or interpreting the tracker.
---

# Deal Tracker — CPI comparison & upside

After a simulation, a deal can be **saved** with the scenario the customer actually closed on
(`engine/deals.py`, persisted by `app/store.py` to `deal_records.json`, gitignored).

## Definitions
- **vs CPI** — compares the *chosen* scenario's total revenue to the *CPI* scenario's:
  `above CPI` (chosen > CPI), `at CPI` (equal), `below CPI` (chosen < CPI), or `no CPI scenario`.
- **Upside vs current** — `chosen revenue − baseline(current) revenue` (the revenue captured above
  today's rates).
- **Upside vs CPI** — `chosen revenue − CPI revenue`.
- The **Deal Tracker** page aggregates: counts at/above/below CPI, total upside, and a per-deal table.

## Rules / assumptions
- The baseline scenario is the simulation's first scenario (usually `current`).
- "At CPI" uses a small relative tolerance so tiny rounding differences read as equal.
- The store may hold customer/commercial data — keep `deal_records.json` out of git.

## Ask the pricing manager
- The customer name and which scenario they closed on.
- Which scenario represents CPI for the comparison (default: the one named `CPI`).
- Any notes to record with the deal.
