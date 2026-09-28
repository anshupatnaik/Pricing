"""Match TOS move keys to BEM (benchmarking) pricing SKUs -> current rates.

Pure logic (no I/O). The data layer fetches effective-today BEM quay rows for a
standardized terminal + operator; this module:
  * parses the TOS ``key`` (e.g. 'Full-Discharge-20', 'Transhipment-Full-40'),
  * keeps only 20/40/45 ft (per reviewer decision), excludes STRGE,
  * chooses the applicable rate sheet (effective today -> latest start date;
    a start+end tie is flagged ambiguous for the user to resolve),
  * matches each move to a BEM SKU (activity priority per category, with a
    blended 'Any' fallback), and
  * applies the per-move / per-cycle basis (BEM & TOS are per single move by
    default -> rate x moves; a 'cycle' activity halves the rate).
"""
from __future__ import annotations

from dataclasses import dataclass

# reviewer decision: only these lengths participate
LENGTH_MAP = {"20": "20 ft", "40": "40 ft", "45": "45 ft"}
GATEWAY_FREIGHT = {"Full", "Empty"}
STORAGE_CATEGORY = "STRGE"

# TOS category -> ordered BEM activity_name candidates (first match wins)
ACTIVITY_PRIORITY = {
    "gateway": ["Load or Discharge Move", "Load or Discharge Move excl Yard Move",
                "Gateway Cycle Move", "Throughput Move (Standard Lift)"],
    "gateway_load": ["Load Move"],
    "gateway_discharge": ["Discharge Move"],
    "Gate": ["Gateway Cycle Move", "Gateway Cycle Move - Import", "Gateway Cycle Move - Export"],
    "Transhipment": ["Transshipment Move", "Transshipment Move - Premium Service"],
    "Restow via quay": ["Restow Move - via Quay", "Restow Move - Via Quay - Premium Service",
                        "Restow Move - Cell to Cell"],
    "Restow on board": ["Restow Move - Cell to Cell", "Restow Move - Cell to Cell - Premium Service",
                        "Restow Move - via Quay"],
    "Truck": ["Gate Move Truck", "Gate Move Truck - Export", "Gate Move Truck - Import",
              "Gate Move Truck - Import - Cabotage (Coastal)", "Gate Move Truck - Additional"],
    "Rail": ["Gate Move Rail"],
}
# activities whose pricing is commonly per full cycle (2 moves); default still per-move
CYCLE_PRONE = {"Transhipment", "Restow via quay", "Restow on board"}

ANY = "Any"


@dataclass(frozen=True)
class MoveAttrs:
    """Parsed TOS key."""
    raw: str
    category: str          # 'gateway' | 'Transhipment' | 'Restow via quay'
    freight: str           # Full | Empty
    direction: str | None  # Load | Discharge | None
    length: str            # '20' | '40' | '45'

    @property
    def length_ft(self) -> str:
        return LENGTH_MAP[self.length]


def parse_tos_key(key: str) -> MoveAttrs | None:
    """Parse a TOS ``key`` into attributes, or None if it should be excluded.

    Excludes storage (STRGE) and any length not in 20/40/45 (per decision).
    """
    if not key:
        return None
    parts = str(key).split("-")
    if len(parts) < 3:
        return None
    first, second, length = parts[0], parts[1], parts[2]
    if first in GATEWAY_FREIGHT:              # 'Full-Discharge-20'
        category, freight, direction = "gateway", first, second
    else:                                      # 'Transhipment-Full-20' / 'Restow via quay-Empty-40' / 'STRGE-...'
        category, freight, direction = first, second, None
    if category == STORAGE_CATEGORY:
        return None
    if length not in LENGTH_MAP:
        return None
    if freight not in GATEWAY_FREIGHT:
        return None
    return MoveAttrs(raw=key, category=category, freight=freight, direction=direction, length=length)


# --------------------------------------------------------------- rate-sheet choice
def _effective(rows, today: str):
    return [r for r in rows
            if str(r.get("EffectiveStartDate") or "") <= today <= str(r.get("EffectiveEndDate") or "9999")]


def choose_rate_sheet(rows, today: str, prefer_id=None):
    """Pick the applicable rate sheet from effective-today BEM rows.

    Returns ``(chosen_rows, info)`` where info has ``ratesheet_id``,
    ``ratesheet_name``, ``ambiguous`` (True when >1 sheet share the latest
    start AND end date -> user must choose), and ``candidates`` (sheet list).
    ``prefer_id`` forces a specific sheet (used to resolve an ambiguous pick).
    """
    eff = _effective(rows, today)
    if not eff:
        return [], {"ratesheet_id": None, "ratesheet_name": None, "ambiguous": False, "candidates": []}
    # group by sheet
    sheets: dict = {}
    for r in eff:
        sid = r.get("RatesheetID") or r.get("RateSheetName")
        s = sheets.setdefault(sid, {"id": sid, "name": r.get("RateSheetName"),
                                    "start": str(r.get("EffectiveStartDate") or ""),
                                    "end": str(r.get("EffectiveEndDate") or ""), "rows": []})
        s["rows"].append(r)
    ranked = sorted(sheets.values(), key=lambda s: s["start"], reverse=True)
    if prefer_id and prefer_id in sheets:
        top = sheets[prefer_id]
        return top["rows"], {"ratesheet_id": top["id"], "ratesheet_name": top["name"],
                             "ambiguous": False,
                             "candidates": [{"id": s["id"], "name": s["name"], "start": s["start"], "end": s["end"]} for s in ranked]}
    top = ranked[0]
    tied = [s for s in ranked if s["start"] == top["start"] and s["end"] == top["end"]]
    ambiguous = len(tied) > 1
    info = {"ratesheet_id": top["id"], "ratesheet_name": top["name"],
            "ambiguous": ambiguous,
            "candidates": [{"id": s["id"], "name": s["name"], "start": s["start"], "end": s["end"]} for s in ranked]}
    return top["rows"], info


# --------------------------------------------------------------- SKU matching
def _candidate_activities(attrs: MoveAttrs) -> list[str]:
    if attrs.category == "gateway":
        acts = list(ACTIVITY_PRIORITY["gateway"])
        if attrs.direction == "Load":
            acts += ACTIVITY_PRIORITY["gateway_load"]
        elif attrs.direction == "Discharge":
            acts += ACTIVITY_PRIORITY["gateway_discharge"]
        return acts
    return ACTIVITY_PRIORITY.get(attrs.category, [])


def match_rate(attrs: MoveAttrs, sheet_rows) -> dict | None:
    """Find the best BEM rate row for a move within a chosen sheet's rows.

    Prefers exact freight+length; falls back to a blended ('Any') row for the
    same activity. Tries activities in priority order.
    """
    length_ft = attrs.length_ft
    for activity in _candidate_activities(attrs):
        cands = [r for r in sheet_rows if r.get("activity_name") == activity]
        if not cands:
            continue
        # 1) exact freight + length
        for r in cands:
            if str(r.get("Freight_Type")) == attrs.freight and str(r.get("Container_Length")) == length_ft:
                return r
        # 2) freight exact, length Any
        for r in cands:
            if str(r.get("Freight_Type")) == attrs.freight and str(r.get("Container_Length")) in (ANY, "None", ""):
                return r
        # 3) fully blended (freight Any, length Any)
        for r in cands:
            if str(r.get("Freight_Type")) in (ANY, "None", "") and str(r.get("Container_Length")) in (ANY, "None", ""):
                return r
    return None


def apply_basis(rate: float, basis: str) -> float:
    """'per_move' -> rate as-is; 'per_cycle' -> rate/2 (convert 2-move price to per-move)."""
    return rate / 2.0 if basis == "per_cycle" else rate


# --------------------------------------------------------------- surcharge / overtime pricing
# The referenced-move activities an OOG/overtime surcharge is priced against; a
# percentage surcharge multiplies the base rate of one of these (per BEM).
LD_ACTIVITIES = ("Load or Discharge Move", "Throughput Move (Standard Lift)",
                 "Load Move", "Discharge Move", "Load or Discharge Move excl Yard Move")
OOG_SURCHARGE_NAMES = ("OOG - Standard or Over height Spreader",)
_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def parse_rate(raw, metric=None) -> tuple[str | None, float | None]:
    """Parse a BEM surcharge/overtime rate to ``(kind, value)``.

    ``'200.00%'`` / ``'200%'`` -> ``('percentage', 2.0)`` (a fraction);
    a bare number (or ``metric='fixed'``) -> ``('fixed', <float>)``;
    ``'NA'`` / ``'On Request'`` / ``''`` / unparseable -> ``(None, None)``.
    """
    s = str(raw or "").strip()
    if not s:
        return (None, None)
    if s.endswith("%"):
        try:
            return ("percentage", float(s[:-1].strip()) / 100.0)
        except ValueError:
            return (None, None)
    if str(metric or "").strip().lower() == "percentage":
        try:
            return ("percentage", float(s) / 100.0)
        except ValueError:
            return (None, None)
    try:
        return ("fixed", float(s))
    except ValueError:
        return (None, None)


def _amount(kind, val, base_rate):
    """Resolve a parsed (kind,val) surcharge to a per-move amount, or None."""
    if kind == "percentage":
        return float(base_rate or 0.0) * val
    if kind == "fixed":
        return val
    return None


def oog_surcharge(sheet_rows, base_ld_rate,
                  surcharge_names=OOG_SURCHARGE_NAMES, ld_activities=LD_ACTIVITIES) -> dict | None:
    """Per-move OOG (standard-spreader) surcharge from chosen surcharge rows.

    Picks an OOG standard-spreader row, preferring one attached to a Load/Discharge
    activity, and resolves it against ``base_ld_rate`` (percentage -> base x pct;
    fixed -> the value). Returns ``{'rate','kind','raw','surcharge_name','activity',
    'currency'}`` or ``None`` when absent / on-request.
    """
    def n(s):
        return str(s or "").strip().lower()

    targets = {n(x) for x in surcharge_names}
    ld = {n(a) for a in ld_activities}
    cands = [r for r in sheet_rows if n(r.get("Surcharge_name")) in targets]
    if not cands:  # looser fallback: any OOG spreader surcharge
        cands = [r for r in sheet_rows
                 if "oog" in n(r.get("Surcharge_name")) and "spreader" in n(r.get("Surcharge_name"))]
    # prefer rows priced against an L/D activity
    cands.sort(key=lambda r: 0 if n(r.get("activity_name")) in ld else 1)
    for r in cands:
        kind, val = parse_rate(r.get("Surcharge_Rate"), r.get("Surcharge_Metric"))
        amount = _amount(kind, val, base_ld_rate)
        if amount is None:
            continue
        return {"rate": amount, "kind": kind, "raw": r.get("Surcharge_Rate"),
                "surcharge_name": r.get("Surcharge_name"), "activity": r.get("activity_name"),
                "currency": r.get("currency")}
    return None


def parse_overtime_indicator(indicator) -> tuple[str, int] | None:
    """``'Monday - 00:00-00:59'`` -> ``('monday', 0)`` (day, start-minute-of-day)."""
    s = str(indicator or "")
    if " - " not in s:
        return None
    day, window = s.split(" - ", 1)
    start = window.split("-", 1)[0].strip()
    try:
        hh, mm = start.split(":")
        return (day.strip().lower(), int(hh) * 60 + int(mm))
    except (ValueError, AttributeError):
        return None


def _to_min(t) -> int | None:
    try:
        hh, mm = str(t).split(":")
        return int(hh) * 60 + int(mm)
    except (ValueError, AttributeError):
        return None


def _day_in_range(day, start_day, end_day) -> bool:
    try:
        di, si, ei = (_DAYS.index(str(x).strip().lower()) for x in (day, start_day, end_day))
    except ValueError:
        return False
    return si <= di <= ei if si <= ei else (di >= si or di <= ei)


def _time_in_range(minute, start_t, end_t) -> bool:
    s, e = _to_min(start_t), _to_min(end_t)
    if s is None or e is None:
        return False
    if s == e:
        return True  # BEM's all-day convention (e.g. '02:00'-'02:00' means the full 24h)
    return s <= minute <= e if s <= e else (minute >= s or minute <= e)


# Overtime for a vessel move applies "on top of" section 2 (Quay Operations) /
# section 3 (Vessel or Marine Operations) only — never Gate (section 4).
OVERTIME_CATEGORIES = ("Quay Operations", "Vessel or Marine Operations")


def overtime_rate(indicator, sheet_rows, base_rate, activities=LD_ACTIVITIES,
                  categories=OVERTIME_CATEGORIES) -> dict | None:
    """Per-move overtime surcharge for a day-hour bucket ``indicator``.

    Overtime is a day/time-banded percentage applied "on top of" the quay-move base
    (rate-sheet sections 2/3). Among overtime rows whose day-band + time-band contain
    the bucket (both bands may wrap midnight / the week) AND whose activity/category
    is a quay or vessel activity, prefers one priced against a vessel L/D activity,
    then any allowed-category row. Resolves against ``base_rate`` (percentage ->
    base x pct; fixed -> value). Gate-Operations rows are never used.
    """
    parsed = parse_overtime_indicator(indicator)
    if not parsed:
        return None
    day, minute = parsed
    acts = {str(a).strip().lower() for a in activities}
    cats = {str(c).strip().lower() for c in categories}

    def eligible(r):
        return (str(r.get("activity_name") or "").strip().lower() in acts
                or str(r.get("category") or "").strip().lower() in cats)

    banded = [r for r in sheet_rows
              if eligible(r)
              and _day_in_range(day, r.get("start_day"), r.get("end_day"))
              and _time_in_range(minute, r.get("start_time"), r.get("end_time"))]
    # prefer an L/D-activity row, then any allowed-category row
    banded.sort(key=lambda r: 0 if str(r.get("activity_name") or "").strip().lower() in acts else 1)
    for r in banded:
        kind, val = parse_rate(r.get("overtime_rate"), r.get("overtime_metric"))
        amount = _amount(kind, val, base_rate)
        if amount is None:
            continue
        return {"rate": amount, "kind": kind, "raw": r.get("overtime_rate"),
                "activity": r.get("activity_name"), "currency": r.get("currency"),
                "band": f"{r.get('start_day')}-{r.get('end_day')} "
                        f"{r.get('start_time')}-{r.get('end_time')}"}
    return None


def average_overtime_uplift(sheet_rows, activities=LD_ACTIVITIES, categories=OVERTIME_CATEGORIES) -> float:
    """Blended overtime uplift % — mean of a full 24x7 hour-of-week grid.

    Mirrors the workbook's ``Overtime`` tab (one row per operator, averaged at
    row 170): every hour of every weekday gets exactly one uplift % — 0% where no
    band applies — and all 168 cells are averaged. This is NOT a mean of the raw
    surcharge rows: those only list hours that carry a premium, so averaging them
    directly silently drops every implicit-0% hour (the majority of a weekday) and
    inflates the result.

    Only recurring Monday-Sunday bands enter the grid — a one-off calendar band
    (``Holidays``, ``Day before Holidays``) has no fixed weekday and can't be
    placed on it, so it's excluded, same as it would be from a real weekly
    average. Eligibility (Quay/Vessel-Marine only, percentage-typed, never Gate)
    matches :func:`overtime_rate`.
    """
    from .overtime import average_uplift
    acts = {str(a).strip().lower() for a in activities}
    cats = {str(c).strip().lower() for c in categories}

    def eligible(r):
        return (str(r.get("activity_name") or "").strip().lower() in acts
                or str(r.get("category") or "").strip().lower() in cats)

    bands = []
    for r in sheet_rows:
        if not eligible(r):
            continue
        sd = str(r.get("start_day") or "").strip().lower()
        ed = str(r.get("end_day") or "").strip().lower()
        if sd not in _DAYS or ed not in _DAYS:
            continue  # one-off calendar band, not a recurring weekday
        kind, val = parse_rate(r.get("overtime_rate"), r.get("overtime_metric"))
        if kind == "percentage" and val is not None:
            bands.append((sd, ed, r.get("start_time"), r.get("end_time"), val))

    grid = []
    for day in _DAYS:
        for hour in range(24):
            minute = hour * 60
            rate = 0.0
            for sd, ed, st, et, val in bands:
                if _day_in_range(day, sd, ed) and _time_in_range(minute, st, et):
                    rate = max(rate, val)
            grid.append(rate)
    return average_uplift(grid)


def rates_for_keys(tos_keys, sheet_rows, basis_by_category=None) -> dict:
    """Map each TOS key to a current per-move rate from the chosen sheet.

    Returns ``{key: {'rate', 'currency', 'sku', 'activity'}}`` for matched keys;
    unmatched/excluded keys are omitted. ``basis_by_category`` optionally sets
    'per_cycle' for a category (default 'per_move').
    """
    basis_by_category = basis_by_category or {}
    out: dict = {}
    for key in tos_keys:
        attrs = parse_tos_key(key)
        if attrs is None:
            continue
        row = match_rate(attrs, sheet_rows)
        if row is None:
            continue
        basis = basis_by_category.get(attrs.category, "per_move")
        try:
            rate = apply_basis(float(row.get("Rate")), basis)
        except (TypeError, ValueError):
            continue
        out[key] = {"rate": rate, "currency": row.get("currency"),
                    "sku": row.get("SKU"), "activity": row.get("activity_name")}
    return out
