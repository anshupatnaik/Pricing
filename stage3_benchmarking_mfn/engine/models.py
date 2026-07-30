"""Immutable data models shared by both simulation modes.

Pure dataclasses, no I/O — mirrors the minimalism of ``dremio_connect``. Two
modes feed a common output (:class:`ScenarioResult` / :class:`SimulationSummary`):

* Detailed (PMS):   occurrences x rate / RoE  ->  SL + BCO revenue, variable cost, margin.
* Simple  (Hapag):  volume x move-share x rate + overtime/surcharges/rebate/storage.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# --- Scenario roles (see engine.methodology) ---------------------------------
ROLE_CURRENT = "current"      # a.k.a. anchor / baseline (comparison base)
ROLE_ANCHOR = "anchor"
ROLE_FLOOR = "floor"
ROLE_TARGET = "target"
ROLE_COMPETITOR = "competitor"
ROLE_CPI = "cpi"
ROLE_CLOSING = "closing"
ROLE_CUSTOM = "custom"
ROLES = (
    ROLE_CURRENT, ROLE_ANCHOR, ROLE_FLOOR, ROLE_TARGET,
    ROLE_COMPETITOR, ROLE_CPI, ROLE_CLOSING, ROLE_CUSTOM,
)

MODE_DETAILED = "detailed"    # PMS occurrence-based
MODE_SIMPLE = "simple"        # Hapag share-based


@dataclass(frozen=True)
class Scenario:
    """A named rate scenario. ``role`` gives it pricing meaning (floor/target/…)."""

    name: str
    role: str = ROLE_CUSTOM


@dataclass(frozen=True)
class ScenarioResult:
    """Per-scenario revenue outcome, common to both modes.

    ``components`` is a mode-specific breakdown (e.g. {"SL": .., "BCO": ..} for
    detailed; {"Quay": .., "Gate": .., "Overtime": ..} for simple). Deltas are
    versus the baseline scenario and filled by :func:`finalize_summary`.
    """

    name: str
    role: str
    total_revenue: float
    total_moves: float
    components: dict[str, float] = field(default_factory=dict)
    variable_cost: float | None = None       # negative (a cost)
    contribution_margin: float | None = None
    # filled in relative to the baseline column
    rpm: float | None = None
    delta_total: float | None = None
    delta_pct: float | None = None


@dataclass(frozen=True)
class SimulationSummary:
    """The tool's output: all scenarios plus which one is the baseline."""

    mode: str
    scenarios: list[ScenarioResult]
    baseline_name: str
    warnings: list[str] = field(default_factory=list)


def finalize_summary(mode, results, baseline_name, warnings=None) -> SimulationSummary:
    """Compute RPM and deltas-vs-baseline for a list of raw ScenarioResults."""
    by_name = {r.name: r for r in results}
    base = by_name.get(baseline_name, results[0] if results else None)
    base_total = base.total_revenue if base else 0.0
    out: list[ScenarioResult] = []
    for r in results:
        rpm = r.total_revenue / r.total_moves if r.total_moves else None
        delta = r.total_revenue - base_total
        pct = (delta / base_total) if base_total else None
        out.append(
            ScenarioResult(
                name=r.name, role=r.role, total_revenue=r.total_revenue,
                total_moves=r.total_moves, components=r.components,
                variable_cost=r.variable_cost, contribution_margin=r.contribution_margin,
                rpm=rpm, delta_total=delta, delta_pct=pct,
            )
        )
    return SimulationSummary(
        mode=mode, scenarios=out,
        baseline_name=base.name if base else "",
        warnings=list(warnings or []),
    )
