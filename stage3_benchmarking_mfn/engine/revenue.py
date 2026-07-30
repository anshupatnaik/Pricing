"""Occurrence-based revenue (PMS mode).

Per the workbook: SL revenue per item/scenario = ``occurrences × rate ÷ RoE``
(``SL Revenue per Ocurrence`` totalled at row 39); BCO revenue = ``occurrences ×
BCO rate`` and is scenario-independent (``Input BCO Revenue!G399``, reused across
all Result columns).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PmsItem:
    """One rate item with its occurrence count and a rate per scenario."""

    group: str
    item: str
    occurrences: float
    rates: dict[str, float] = field(default_factory=dict)   # scenario name -> rate
    vessel_move: bool = True
    bco_rate: float = 0.0


def sl_revenue(items, scenario_names, roe: float = 1.0) -> dict[str, float]:
    """Total SL revenue per scenario = Σ occurrences × rate ÷ RoE."""
    roe = roe or 1.0
    return {
        s: sum(it.occurrences * float(it.rates.get(s, 0.0) or 0.0) / roe for it in items)
        for s in scenario_names
    }


def sl_revenue_per_item(items, scenario_names, roe: float = 1.0) -> list[dict]:
    """Per-item SL revenue for each scenario (the 'SL Revenue per Ocurrence' view).

    Each row = Item #, Group, Item, Vessel Move?, Occurrences, then revenue per
    scenario (``occurrences × rate ÷ RoE``). Column sums equal :func:`sl_revenue`.
    """
    roe = roe or 1.0
    out: list[dict] = []
    for i, it in enumerate(items, start=1):
        row = {
            "Item #": i, "Group": it.group, "Item": it.item,
            "Vessel Move?": "YES" if it.vessel_move else "NO",
            "Occurrences": it.occurrences,
        }
        for s in scenario_names:
            row[s] = it.occurrences * float(it.rates.get(s, 0.0) or 0.0) / roe
        out.append(row)
    return out


def bco_revenue(items) -> float:
    """Total BCO revenue (scenario-independent) = Σ occurrences × BCO rate."""
    return sum(it.occurrences * (it.bco_rate or 0.0) for it in items)


def total_vessel_moves(items) -> float:
    """Sum of occurrences flagged as vessel moves (the RPM denominator)."""
    return sum(it.occurrences for it in items if it.vessel_move)
