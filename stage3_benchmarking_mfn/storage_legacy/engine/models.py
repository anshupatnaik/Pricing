"""Immutable data models for the storage-revenue simulation engine.

These are plain dataclasses with no I/O, no network and no third-party deps, so
the engine can be unit-tested in isolation (mirrors the minimalism of the
existing ``dremio_connect`` package). All monetary values are floats in the
terminal's own currency; ``container_count`` is kept as a float because Dremio
returns numeric measures as floats.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# The four cargo streams the workbook models (same Dremio table, different
# filters). Kept as constants so the data layer and UI agree on spelling.
CARGO_DRY = "Dry"
CARGO_REEFER = "Reefer"
CARGO_OOG = "OOG"
CARGO_HAZARDOUS = "Hazardous"
CARGO_TYPES = (CARGO_DRY, CARGO_REEFER, CARGO_OOG, CARGO_HAZARDOUS)

# Calculation methods (workbook cell B12 on each simulation sheet).
METHOD_CONTAINER = "Container"
METHOD_TEU_SIMPLE = "TEU Simple"
METHOD_TEU_ADVANCED = "TEU Advanced"
METHODS = (METHOD_CONTAINER, METHOD_TEU_SIMPLE, METHOD_TEU_ADVANCED)

# Storage day tiers run Day 0 .. Day 45 inclusive; beyond that the workbook
# charges each extra day at the Day-45 rate (see engine.rates).
MAX_DAY = 45


@dataclass(frozen=True)
class RawRow:
    """One pre-aggregated occurrence row from ``GBL_Storage_Excel_Simulator``.

    Rows are already grouped by terminal x operator x category x dwell-day x
    length, so ``container_count`` is the number of containers sharing these
    attributes.
    """

    category: str            # unit_category_fixed: Import / Export / Transshipment
    freight_kind: str        # freight_kind (always 'Full' after the query filter)
    dwell_days: int
    container_count: float
    container_length: float   # 20 / 40 / 45 ...
    operator: str = ""
    terminal: str = ""
    cargo_type: str = ""      # which stream this row belongs to (Dry/Reefer/...)


@dataclass(frozen=True)
class ScenarioRevenue:
    """Revenue for a single rate column (baseline or one scenario).

    ``index`` 0 is the baseline (workbook column H); 1..8 map to Scenario 1..8
    (columns I..P). Deltas are measured against the baseline.
    """

    index: int
    name: str
    by_category: dict[str, float]
    total: float
    delta_by_category: dict[str, float]
    delta_total: float
    # None where the baseline is zero (workbook writes "N/A").
    delta_pct_by_category: dict[str, float | None]
    delta_pct_total: float | None


@dataclass(frozen=True)
class SimulationReport:
    """Full result of a simulation: the baseline plus every defined scenario."""

    categories: list[str]
    baseline: ScenarioRevenue
    scenarios: list[ScenarioRevenue]
    method: str
    warnings: list[str] = field(default_factory=list)

    @property
    def all_columns(self) -> list[ScenarioRevenue]:
        """Baseline first, then scenarios in order (handy for tables)."""
        return [self.baseline, *self.scenarios]
