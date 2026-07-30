"""Parse an uploaded rate sheet into Current rates for the simple model.

Accepts a DataFrame (from CSV/XLSX) plus the chosen item and rate columns, and
fuzzy-matches each row to a model line by keyword. Everything is overridable in
the UI afterwards, so matching only needs to be a good first guess.
"""
from __future__ import annotations

# model line -> keywords to look for in the rate sheet's item text
LINE_ALIASES = {
    "full_ld": ["load/disc full", "load disc full", "l/d full", "loaded full", "full l/d", "discharge full", "load full"],
    "empty_ld": ["load/disc empty", "load disc empty", "l/d empty", "empty l/d", "discharge empty", "load empty"],
    "transhipment": ["transhipment", "transshipment", "trshp", "t/s"],
    "shift": ["shift", "restow", "thrgh", "through"],
    "gate_full": ["gate full", "gw full", "gateway full"],
    "gate_empty": ["gate empty", "gw empty", "gateway empty"],
    "reefer": ["reefer", "plugin", "plug-in", "reefer dwell"],
}


def _num(v):
    try:
        return float(str(v).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None


def _norm_item(s) -> str:
    return " ".join(str(s or "").strip().lower().replace("_", "-").split())


def parse_rate_sheet_by_item(df, item_col: str, rate_col: str, items) -> dict[str, float]:
    """Map a rate sheet to an explicit list of item keys (detailed/PMS mode).

    Matches on the normalized item string (case/space/underscore-insensitive),
    first by exact match then by substring. Returns {item: rate} for matches.
    """
    lookup = {}
    for _, row in df.iterrows():
        key = _norm_item(row.get(item_col))
        rate = _num(row.get(rate_col))
        if key and rate is not None and key not in lookup:
            lookup[key] = rate
    out: dict[str, float] = {}
    for item in items:
        nk = _norm_item(item)
        if nk in lookup:
            out[item] = lookup[nk]
            continue
        for k, v in lookup.items():          # fall back to substring match
            if nk and (nk in k or k in nk):
                out[item] = v
                break
    return out


def parse_rate_sheet(df, item_col: str, rate_col: str) -> dict[str, float]:
    """Return {line: rate} by fuzzy-matching the sheet's item column to model lines.

    First match per line wins. Lines with no match are omitted (left for the
    manager to fill).
    """
    pairs = []
    for _, row in df.iterrows():
        item = str(row.get(item_col, "")).strip().lower()
        rate = _num(row.get(rate_col))
        if item and rate is not None:
            pairs.append((item, rate))

    out: dict[str, float] = {}
    for line, aliases in LINE_ALIASES.items():
        for item, rate in pairs:
            if any(a in item for a in aliases):
                out[line] = rate
                break
    return out
