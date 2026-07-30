"""Core storage-revenue calculation — a faithful port of the workbook VBA.

For each pre-aggregated occurrence row we pick the rate block for its category,
sum the daily rates across the container's dwell days, scale by container count
and the TEU factor, and accumulate per category and per rate column
(baseline + scenarios). See reference/vba_dump/all_modules.vba for the original
``Calculate_Revenue_Summary_*`` subroutines this mirrors.

Matching rules (VBA-faithful):
  * exact match  -> a "Day <dwell>" row exists in the row's category block
    (always true for dwell 0..45). Revenue = sum(rates 0..dwell).
  * over-45 fallback -> only fires when the block's *type* equals the row's
    freight_kind (this is why, in the basic sheets where the block type is the
    cargo type e.g. "Dry" and freight_kind is "Full", dwell>45 rows contribute
    nothing). Revenue = sum(rates 0..45) + (dwell-45)*rate[45].
"""
from __future__ import annotations

from .models import MAX_DAY, RawRow, ScenarioRevenue, SimulationReport
from .rates import RateSchedule
from .teu import teu_factor


def _should_compute(block, row: RawRow) -> bool:
    """Whether this row produces revenue for its category block (see module doc)."""
    if block is None:
        return False
    if 0 <= row.dwell_days <= MAX_DAY and block.has_day(row.dwell_days):
        return True  # matchFound
    return block.type_ == row.freight_kind  # secondMatch fallback


def row_revenue(row: RawRow, schedule: RateSchedule, method: str) -> list[float]:
    """Revenue contribution of one row for every column (baseline + scenarios).

    Returns a list of length ``schedule.n_cols``; all zeros when the row has no
    matching/eligible rate block.
    """
    block = schedule.block(row.category)
    if not _should_compute(block, row):
        return [0.0] * schedule.n_cols
    factor = teu_factor(row.container_length, method) * row.container_count
    return [block.cumulative(row.dwell_days, col) * factor for col in range(schedule.n_cols)]


def build_report(
    by_cat: dict[str, list[float]],
    totals: list[float],
    method: str,
    scenario_names=None,
    warnings=None,
) -> SimulationReport:
    """Assemble a :class:`SimulationReport` from accumulated per-column revenue.

    ``by_cat`` maps each category to a list of revenue-per-column (index 0 is the
    baseline); ``totals`` is the same list summed across categories. Shared by
    :func:`run_simulation` and the reefer-additional calculation.
    """
    n_cols = len(totals)
    categories = sorted(by_cat)

    def make_column(col: int, name: str) -> ScenarioRevenue:
        base_by_cat = {c: by_cat[c][0] for c in categories}
        cur_by_cat = {c: by_cat[c][col] for c in categories}
        delta_by_cat = {c: cur_by_cat[c] - base_by_cat[c] for c in categories}
        pct_by_cat = {
            c: (delta_by_cat[c] / base_by_cat[c] if base_by_cat[c] else None)
            for c in categories
        }
        delta_total = totals[col] - totals[0]
        pct_total = delta_total / totals[0] if totals[0] else None
        return ScenarioRevenue(
            index=col,
            name=name,
            by_category=cur_by_cat,
            total=totals[col],
            delta_by_category=delta_by_cat,
            delta_total=delta_total,
            delta_pct_by_category=pct_by_cat,
            delta_pct_total=pct_total,
        )

    names = list(scenario_names or [])
    baseline = make_column(0, "Baseline")
    scenarios = [
        make_column(col, names[col - 1] if col - 1 < len(names) else f"Scenario {col}")
        for col in range(1, n_cols)
    ]
    return SimulationReport(
        categories=categories,
        baseline=baseline,
        scenarios=scenarios,
        method=method,
        warnings=list(warnings or []),
    )


def run_simulation(
    rows,
    schedule: RateSchedule,
    method: str,
    scenario_names=None,
) -> SimulationReport:
    """Aggregate revenue over all rows into a :class:`SimulationReport`.

    ``rows`` is an iterable of :class:`RawRow`. Revenue is bucketed by the row's
    ``category`` and by rate column; deltas are computed against the baseline
    (column 0).
    """
    n_cols = schedule.n_cols
    by_cat: dict[str, list[float]] = {}
    totals = [0.0] * n_cols
    unmatched = 0

    for row in rows:
        block = schedule.block(row.category)
        contrib = row_revenue(row, schedule, method)
        if block is None or not _should_compute(block, row):
            unmatched += 1
        bucket = by_cat.setdefault(row.category, [0.0] * n_cols)
        for col in range(n_cols):
            bucket[col] += contrib[col]
            totals[col] += contrib[col]

    warnings = []
    if unmatched:
        warnings.append(
            f"{unmatched} row(s) produced no revenue (no matching rate block, "
            f"or dwell>45 with a non-matching block type)."
        )
    return build_report(by_cat, totals, method, scenario_names, warnings)
