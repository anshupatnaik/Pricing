"""Assemble the PMS (detailed) Result summary across scenarios.

Mirrors the workbook ``Result`` sheet: per scenario -> SL Revenue, BCO Revenue,
Total Revenue, Variable Cost (``var_cost_per_move × moves``; a negative number),
Contribution Margin, and per-move metrics; deltas vs the baseline scenario are
added by :func:`engine.models.finalize_summary`.
"""
from __future__ import annotations

from .models import MODE_DETAILED, ScenarioResult, finalize_summary
from .revenue import bco_revenue, sl_revenue, total_vessel_moves


def run_detailed(
    items,
    scenarios,
    roe: float = 1.0,
    var_cost_per_move: float = 0.0,
    total_moves: float | None = None,
    include_bco: bool = True,
    baseline_name: str | None = None,
):
    """Run the occurrence-based model -> SimulationSummary.

    ``items`` are :class:`engine.revenue.PmsItem`; ``scenarios`` are
    :class:`engine.models.Scenario`. ``var_cost_per_move`` should be negative
    (a cost), matching the workbook's ``Input Filters!F27``.
    """
    names = [s.name for s in scenarios]
    sl = sl_revenue(items, names, roe)
    bco = bco_revenue(items) if include_bco else 0.0
    moves = total_vessel_moves(items) if total_moves is None else total_moves

    results = []
    for sc in scenarios:
        slr = sl[sc.name]
        total = slr + bco
        var_cost = var_cost_per_move * moves
        cm = total + var_cost
        results.append(
            ScenarioResult(
                name=sc.name, role=sc.role, total_revenue=total, total_moves=moves,
                components={"SL": slr, "BCO": bco}, variable_cost=var_cost,
                contribution_margin=cm,
            )
        )
    baseline = baseline_name or (scenarios[0].name if scenarios else "")
    return finalize_summary(MODE_DETAILED, results, baseline)
