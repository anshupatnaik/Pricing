"""Derive billable occurrences from vessel-moves rows (PMS mode).

Ports the workbook's ``Automatic Ocurrences`` logic: the moves key is
``UNIT_FREIGHT_GROUP-event_type-cont_length`` (e.g. ``Full-Load-40``) and an
item's occurrences are ``SUMIF(key, total_moves)``. Hazardous-surcharge
occurrences (VBA ``PopulateUniqueSLRatesAndOccurrences``) combine the
``imo_indicator`` and rounded ``cargo_imdg_types`` into
``"<imo> <imdg> Load/Discharge"``.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OccurrenceRow:
    item: str
    count: float
    group: str = ""
    vessel_move: bool = True
    annualized: float | None = None


#: Single OOG-surcharge item label (matches the vUSA PMS workbook, item 41).
OOG_ITEM = "OOG with spreader or slings"


def _norm_length(cont_length):
    """Normalise a container length (40.0 -> 40), leaving non-numeric values as-is."""
    try:
        return int(float(cont_length))
    except (TypeError, ValueError):
        return cont_length


def move_key(freight_group: str, event_type: str, cont_length) -> str:
    """Build the occurrence key, e.g. ('Full','Load',40) -> 'Full-Load-40'."""
    return f"{freight_group}-{event_type}-{_norm_length(cont_length)}"


def gate_key(mode_label: str, freight_group: str, cont_length) -> str:
    """Build a gate-move key, e.g. ('Rail','Full',40) -> 'Rail-Full-40'.

    ``mode_label`` is the workbook group prefix ('Truck' or 'Rail').
    """
    return f"{mode_label}-{freight_group}-{_norm_length(cont_length)}"


def _round_imdg(imdg_types: str) -> str:
    parts = []
    for p in str(imdg_types).split(","):
        p = p.strip()
        try:
            parts.append(str(int(float(p))))
        except (TypeError, ValueError):
            continue
    return ",".join(parts)


def hazard_key(imo_indicator: str, imdg_types: str) -> str:
    return f"{imo_indicator} {_round_imdg(imdg_types)} Load/Discharge"


def _days_between(date_from, date_to) -> int | None:
    """Inclusive day count between two Excel serials / ISO dates, else None."""
    try:
        return int(float(date_to)) - int(float(date_from)) + 1
    except (TypeError, ValueError):
        pass
    try:
        from datetime import date

        def parse(d):
            y, m, dd = str(d)[:10].split("-")
            return date(int(y), int(m), int(dd))

        return (parse(date_to) - parse(date_from)).days + 1
    except Exception:
        return None


def annualize(count: float, days: int | None) -> float | None:
    """Scale an occurrence count to a full year (``count*365/days``)."""
    if not days:
        return None
    return count * 365.0 / days


def derive_occurrences(
    moves_rows,
    freight_col="unit_freight_group",
    event_col="event_type",
    length_col="cont_length",
    count_col="total_moves",
    date_from=None,
    date_to=None,
    include_hazard=True,
    imo_col="imo_indicator",
    imdg_col="cargo_imdg_types",
) -> list[OccurrenceRow]:
    """Aggregate moves rows into occurrence rows keyed by move key (+ hazard).

    ``moves_rows`` is an iterable of dict-like rows (as returned by the Dremio
    client). Column names default to the ``GBL_moves_simulator`` schema.
    """
    days = _days_between(date_from, date_to)
    sums: dict[str, float] = {}
    hazard: dict[str, float] = {}
    for r in moves_rows:
        fg = r.get(freight_col)
        ev = r.get(event_col)
        ln = r.get(length_col)
        try:
            cnt = float(r.get(count_col) or 0.0)
        except (TypeError, ValueError):
            cnt = 0.0
        if fg and ev and ln not in (None, ""):
            sums[move_key(fg, ev, ln)] = sums.get(move_key(fg, ev, ln), 0.0) + cnt
        if include_hazard:
            imo = r.get(imo_col)
            imdg = r.get(imdg_col)
            if imo and imdg:
                k = hazard_key(imo, imdg)
                hazard[k] = hazard.get(k, 0.0) + cnt

    out = [
        OccurrenceRow(item=k, count=v, group="Vessel Moves-Gateway",
                      vessel_move=True, annualized=annualize(v, days))
        for k, v in sums.items()
    ]
    out += [
        OccurrenceRow(item=k, count=v, group="Surcharge - Hazardous Cargo",
                      vessel_move=False, annualized=annualize(v, days))
        for k, v in hazard.items()
    ]
    return out
