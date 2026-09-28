"""Assemble the PMS (detailed) Result summary across scenarios.

Mirrors the workbook ``Result`` sheet: per scenario -> SL Revenue, BCO Revenue,
Total Revenue, Variable Cost (``var_cost_per_move × moves``; a negative number),
Contribution Margin, and per-move metrics; deltas vs the baseline scenario are
added by :func:`engine.models.finalize_summary`.
"""
from __future__ import annotations

from .models import MODE_DETAILED, ScenarioResult, finalize_summary
from .revenue import bco_revenue, quay_revenue, sl_revenue, total_vessel_moves


def run_detailed(
    items,
    scenarios,
    roe: float = 1.0,
    var_cost_per_move: float = 0.0,
    total_moves: float | None = None,
    include_bco: bool = True,
    baseline_name: str | None = None,
    overtime_uplift_pct: float | None = None,
    storage_revenue: dict[str, float] | None = None,
    empty_storage_revenue: dict[str, float] | None = None,
    reefer_revenue: dict[str, float] | None = None,
):
    """Run the occurrence-based model -> SimulationSummary.

    ``items`` are :class:`engine.revenue.PmsItem`; ``scenarios`` are
    :class:`engine.models.Scenario`. ``var_cost_per_move`` should be negative
    (a cost), matching the workbook's ``Input Filters!F27``.

    ``overtime_uplift_pct``, when given, adds a blended overtime line
    (``quay_revenue[scenario] × pct``, see :func:`engine.revenue.quay_revenue`) as
    an ``"OT"`` component — the alternative to per-bucket banded overtime items
    (leave ``None``, the default, when overtime is instead modelled as individual
    day-hour occurrence items with their own rates).

    ``storage_revenue`` / ``empty_storage_revenue`` / ``reefer_revenue``, when
    given, are each a per-scenario ``{name: amount}`` dict (see
    :func:`engine.storage.total_storage_revenue` / :func:`engine.storage.pool_revenue`
    / :func:`engine.reefer.reefer_revenue`, one call per scenario against that
    scenario's own tariff) added as separate ``"Storage"`` / ``"EmptyStorage"``
    / ``"Reefer"`` components, so each stays individually visible in the
    summary rather than merged into one number. A scenario absent from a dict
    gets 0 for that component.
    """
    names = [s.name for s in scenarios]
    sl = sl_revenue(items, names, roe)
    bco = bco_revenue(items) if include_bco else 0.0
    moves = total_vessel_moves(items) if total_moves is None else total_moves
    ot = None
    if overtime_uplift_pct is not None:
        quay = quay_revenue(items, names, roe)
        ot = {s: quay[s] * overtime_uplift_pct for s in names}

    results = []
    for sc in scenarios:
        slr = sl[sc.name]
        ot_amt = ot[sc.name] if ot is not None else 0.0
        storage_amt = (storage_revenue or {}).get(sc.name, 0.0)
        empty_amt = (empty_storage_revenue or {}).get(sc.name, 0.0)
        reefer_amt = (reefer_revenue or {}).get(sc.name, 0.0)
        total = slr + ot_amt + storage_amt + empty_amt + reefer_amt + bco
        var_cost = var_cost_per_move * moves
        cm = total + var_cost
        components = {"SL": slr, "BCO": bco}
        if ot is not None:
            components["OT"] = ot_amt
        if storage_revenue is not None:
            components["Storage"] = storage_amt
        if empty_storage_revenue is not None:
            components["EmptyStorage"] = empty_amt
        if reefer_revenue is not None:
            components["Reefer"] = reefer_amt
        results.append(
            ScenarioResult(
                name=sc.name, role=sc.role, total_revenue=total, total_moves=moves,
                components=components, variable_cost=var_cost,
                contribution_margin=cm,
            )
        )
    baseline = baseline_name or (scenarios[0].name if scenarios else "")
    return finalize_summary(MODE_DETAILED, results, baseline)
