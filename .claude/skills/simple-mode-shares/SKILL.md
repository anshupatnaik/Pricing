---
name: simple-mode-shares
description: How move-type shares are computed from Dremio for the Stage-3 SL revenue simulator simple (Hapag) mode (gateway/transhipment/shift/reefer splits, STRGE excluded). Use when prefilling or reviewing shares, or explaining the volume mix.
---

# Simple-mode move-type shares

Each share = (that move type's moves) ÷ **TOP**, where TOP = total vessel moves **excluding
storage** (`STRGE`). Computed by `engine/shares.py`; prefilled via `repository.get_shares`.

## Category → share mapping (validated against the manager's pivot)
| Share | From `category` (+ `unit_freight_group`) |
|-------|------------------------------------------|
| `full_ld` / `gate_full` | (Import + Export) **Full** |
| `empty_ld` / `gate_empty` | (Import + Export) **Empty** |
| `transhipment` | category `Transhipment` |
| `shift` | category `Restow via quay` (the pivot's "THRGH") |
| `reefer` | `reefer_indicator = 'Live Reefers'` (cross-cut) |
| `oog` / `imo` | `oog_indicator` / `imo_indicator` set (cross-cut) |

`STRGE` (storage) is excluded from TOP. `reefer_dwell` is a **day count**, not a share, and stays
a manual input. Example: TRSHP 37,757 / TOP 50,791 = 74%.

## Rules / assumptions
- Reefer/OOG/IMO are **cross-cuts** (a move can be reefer *and* gateway), so their shares are
  computed over the same TOP and are not part of the gateway/transhipment/shift partition.
- Gate shares equal the gateway full/empty shares (gate moves = gateway moves).
- Shares are a prefill; the manager can override any value.

## Ask the pricing manager
- The terminal/operators/date range to compute shares from (usually a prior actual year).
- Whether to accept the Dremio-derived shares or override any (e.g. for a forecast mix).
- The reefer dwell (days) to apply.
