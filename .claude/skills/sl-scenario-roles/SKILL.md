---
name: sl-scenario-roles
description: Meaning of the SL rate-scenario roles (current/anchor, floor, target, competitor, CPI, closing) and the floor<=anchor<=target invariant used across the Stage-3 SL revenue simulator. Use when defining, naming, deriving, or validating rate scenarios, or prompting a pricing manager for scenario rates.
---

# SL scenario roles

Scenarios are named rate columns. The **first scenario is the baseline** all deltas compare
against. Roles give a scenario pricing meaning (see `engine/methodology.py` — the single source
of role logic).

| Role | Meaning | Typical derivation |
|------|---------|--------------------|
| `current` / `anchor` | Rates charged today; negotiation opening point; **the baseline**. | Manager-entered actuals. |
| `floor` | Walk-away minimum acceptable rates. | Anchor × factor, or entered. |
| `target` | Aspirational rates management wants. | Anchor × uplift, or entered. |
| `competitor` | A benchmark line's rates (MFN-style reference). | Entered from market intel. |
| `cpi` | Anchor escalated by inflation: `rate × (1 + CPI)`. | `methodology.cpi_escalate`. |
| `closing` | The agreed closing rates. | Entered at deal close. |

## Rules / assumptions
- **Invariant:** at every line item `floor <= anchor <= target`. Validate with
  `methodology.validate_ordering(...)` and warn (do not silently accept) violations.
- CPI escalation is multiplicative: `rate × (1 + cpi)`.
- Roles are labels only — the engine treats every scenario as a rate curve; never hard-code role
  behaviour outside `engine/methodology.py`.

## How rates are set (app flow)
- **Current** rates are entered directly or by **uploading a rate sheet** (CSV/XLSX) which the tool
  parses into the Current column (`app/ratesheet.py`).
- **Every other scenario** derives from Current by a single **% in the scenarios table**:
  `rate = current × (1 + pct)` (`methodology.derive_from_pct`). Each scenario row also carries a
  free-text **comment**.
- **Override always wins:** any per-line rate the manager types in the override grid replaces the
  derived value. Derivation is only a starting point.

## Ask the pricing manager
- Which scenario is the baseline (default: the one named/roled `current`)?
- The % to apply for each scenario (floor is typically negative; target/anchor positive) and a comment.
- The CPI % to use for any `cpi` scenario.
- Whether to upload a rate sheet for Current, or type rates; and any per-line overrides.
- Whether a competitor/MFN reference column should be included and its source.
