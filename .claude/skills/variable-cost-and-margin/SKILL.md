---
name: variable-cost-and-margin
description: Variable-cost-per-move sign convention and contribution-margin calculation in the Stage-3 SL revenue simulator (detailed/PMS mode). Use when entering variable cost, computing contribution margin, or interpreting the Result summary.
---

# Variable cost & contribution margin (detailed mode)

From the workbook `Result` sheet:

    variable_cost      = var_cost_per_move × total_vessel_moves   (a NEGATIVE number)
    total_revenue      = SL revenue + BCO revenue
    contribution_margin = total_revenue + variable_cost           (i.e. revenue minus cost)

## Rules / assumptions
- **`var_cost_per_move` is entered as a negative number** (workbook `Input Filters!F27`, e.g.
  `-32`). The engine adds it, so margin = revenue − cost.
- Variable cost scales with **total vessel moves** (the same denominator as RPM), not occurrences.
- Per-move metrics divide by total vessel moves; guard against zero moves (RPM/margin-per-move
  are undefined and shown blank).
- The workbook's `Variable Cost` sheet contains `#REF!` errors; we implement the intended
  `var_cost_per_move × moves` logic from `Result` and do **not** replicate the broken cells.

## Ask the pricing manager
- Variable cost per move (negative), or the total variable cost to back into per-move.
- Whether contribution margin should be shown per scenario (default: yes).
