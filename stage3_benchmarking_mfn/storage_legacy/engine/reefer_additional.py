"""Live Reefer Additional Charges (Electricity + Other Charges).

Port of ``Calculate_Revenue_Summary_reefer_electricity`` (see
reference/vba_dump/all_modules.vba). Unlike the basic simulations this runs on
*every* reefer row and computes two independent charge streams, each with its
own Day 0..45 rate block, keyed by charge kind ("Electricity" / "Other
Charges") rather than by cargo category. The over-45 fallback here fires
whenever the block exists (there is no freight_kind gate), so long-dwell
containers are charged the Day-45 rate for extra days.
"""
from __future__ import annotations

from .models import SimulationReport
from .rates import RateSchedule
from .revenue import build_report
from .teu import teu_factor

ELECTRICITY = "Electricity"
OTHER_CHARGES = "Other Charges"


def reefer_additional(rows, schedule: RateSchedule, method: str, scenario_names=None) -> SimulationReport:
    """Aggregate reefer electricity + other charges into a report.

    ``schedule`` must contain blocks keyed ``"Electricity"`` and
    ``"Other Charges"``. Categories in the returned report are those two charge
    kinds; the total is their sum.
    """
    n_cols = schedule.n_cols
    by_cat: dict[str, list[float]] = {}
    totals = [0.0] * n_cols

    for row in rows:
        factor = teu_factor(row.container_length, method) * row.container_count
        for kind in (ELECTRICITY, OTHER_CHARGES):
            block = schedule.block(kind)
            if block is None:
                continue
            bucket = by_cat.setdefault(kind, [0.0] * n_cols)
            for col in range(n_cols):
                rev = block.cumulative(row.dwell_days, col) * factor
                bucket[col] += rev
                totals[col] += rev

    return build_report(by_cat, totals, method, scenario_names)
