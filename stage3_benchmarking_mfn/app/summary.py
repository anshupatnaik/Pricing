"""Turn a SimulationSummary into a tidy DataFrame for display / export."""
from __future__ import annotations

import pandas as pd

from engine.models import MODE_DETAILED, SimulationSummary


def summary_to_frame(summary: SimulationSummary) -> pd.DataFrame:
    """One row per scenario with the headline metrics + deltas.

    Detailed mode shows revenue/RPM/margin **with and without BCO** so managers
    can compare (BCO = Σ occurrences × revenue-per-occurrence).
    """
    rows = []
    for r in summary.scenarios:
        moves = r.total_moves or 0.0
        if summary.mode == MODE_DETAILED:
            sl = r.components.get("SL", 0.0) or 0.0
            ot = r.components.get("OT", 0.0) or 0.0
            storage = r.components.get("Storage", 0.0) or 0.0
            empty_storage = r.components.get("EmptyStorage", 0.0) or 0.0
            reefer = r.components.get("Reefer", 0.0) or 0.0
            bco = r.components.get("BCO", 0.0) or 0.0
            vc = r.variable_cost or 0.0
            total_excl = sl + ot + storage + empty_storage + reefer
            total_incl = sl + ot + storage + empty_storage + reefer + bco
            row = {
                "Scenario": r.name, "Role": r.role, "Total Moves": moves,
                "SL Revenue": sl, "Overtime (blended)": ot, "Storage Revenue": storage,
                "Empty Storage Revenue": empty_storage, "Reefer Revenue": reefer,
                "BCO Revenue": bco,
                "Total Revenue (excl BCO)": total_excl,
                "Total Revenue (incl BCO)": total_incl,
                "RPM (excl BCO)": (total_excl / moves) if moves else None,
                "RPM (incl BCO)": (total_incl / moves) if moves else None,
                "Variable Cost": vc,
                "Contribution Margin (excl BCO)": total_excl + vc,
                "Contribution Margin (incl BCO)": total_incl + vc,
                "Δ Revenue vs baseline (incl BCO)": r.delta_total,
                "Δ %": None if r.delta_pct is None else r.delta_pct * 100.0,
            }
        else:
            row = {
                "Scenario": r.name, "Role": r.role, "Total Moves": moves,
                "Total Revenue": r.total_revenue, "RPM": r.rpm,
                "Δ Revenue vs baseline": r.delta_total,
                "Δ %": None if r.delta_pct is None else r.delta_pct * 100.0,
            }
            for k in ("Quay", "Gate", "Reefer", "Overtime", "IMO", "OOG", "Rebate", "Storage"):
                if k in r.components:
                    row[k] = r.components[k]
        rows.append(row)
    return pd.DataFrame(rows).set_index("Scenario")


def components_frame(summary: SimulationSummary) -> pd.DataFrame:
    """Scenario x component matrix (for a breakdown chart)."""
    data = {r.name: r.components for r in summary.scenarios}
    return pd.DataFrame(data).T
