"""Compute simple-mode move-type shares from Dremio move counts.

Share of each move type = (its moves) / TOP, where TOP is total vessel moves
excluding storage (``STRGE``). Mapping (validated against the manager's pivot):

    GW Full      = Import Full  + Export Full        -> gate_full / full_ld
    GW Empty     = Import Empty + Export Empty        -> gate_empty / empty_ld
    Transhipment = category 'Transhipment'            -> transhipment
    Shift        = category 'Restow via quay'         -> shift  (a.k.a. THRGH)
    Reefer       = reefer_indicator = 'Live Reefers'  -> reefer (cross-cut)
    OOG / IMO    = oog_indicator / imo_indicator set  -> oog / imo (cross-cut)

Example (manager's numbers): TRSHP 37,757 / TOP 50,791 = 74%.
"""
from __future__ import annotations

GATEWAY_CATEGORIES = {"import", "export"}
TRANSHIPMENT_CATEGORIES = {"transhipment", "transshipment"}
SHIFT_CATEGORIES = {"restow via quay"}
EXCLUDED_CATEGORIES = {"strge", "storage"}
FULL_VALUES = {"full", "fcl"}


def _norm(s) -> str:
    return str(s or "").strip().lower()


def compute_shares(
    category_rows,
    reefer_moves: float = 0.0,
    oog_moves: float = 0.0,
    imo_moves: float = 0.0,
    reefer_dwell: float = 1.0,
) -> dict:
    """Return the simple-model shares dict from category/freight move counts.

    ``category_rows`` is an iterable of dicts with ``category``,
    ``unit_freight_group`` and ``total_moves`` (already summed). ``reefer_moves``
    / ``oog_moves`` / ``imo_moves`` are scalar totals over the same population.
    ``reefer_dwell`` passes through unchanged (it is a day count, not a share).
    """
    gw_full = gw_empty = transhipment = shift = 0.0
    top = 0.0
    for r in category_rows:
        cat = _norm(r.get("category"))
        if cat in EXCLUDED_CATEGORIES:
            continue
        moves = float(r.get("total_moves") or 0.0)
        is_full = _norm(r.get("unit_freight_group")) in FULL_VALUES
        top += moves
        if cat in GATEWAY_CATEGORIES:
            if is_full:
                gw_full += moves
            else:
                gw_empty += moves
        elif cat in TRANSHIPMENT_CATEGORIES:
            transhipment += moves
        elif cat in SHIFT_CATEGORIES:
            shift += moves
        # any other non-excluded category still counts toward TOP only

    def share(x):
        return x / top if top else 0.0

    return {
        "full_ld": share(gw_full),
        "empty_ld": share(gw_empty),
        "gate_full": share(gw_full),
        "gate_empty": share(gw_empty),
        "transhipment": share(transhipment),
        "shift": share(shift),
        "reefer": share(reefer_moves),
        "oog": share(oog_moves),
        "imo": share(imo_moves),
        "reefer_dwell": reefer_dwell,
        "_top_moves": top,
    }
