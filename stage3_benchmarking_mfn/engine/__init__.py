"""Pure SL revenue-simulation engine (no I/O, no network, no UI).

Two modes share a common output (:class:`SimulationSummary`):
  * Detailed (PMS)  - engine.occurrences + engine.revenue + engine.result
  * Simple  (Hapag) - engine.simple_model
Plus engine.overtime and engine.methodology (scenario roles / rate derivations).
"""
from __future__ import annotations

from . import deals, methodology, overtime, pricing, shares
from .models import (
    MODE_DETAILED,
    MODE_SIMPLE,
    ROLES,
    Scenario,
    ScenarioResult,
    SimulationSummary,
    finalize_summary,
)
from .occurrences import OccurrenceRow, derive_occurrences, move_key
from .revenue import PmsItem, bco_revenue, sl_revenue, sl_revenue_per_item, total_vessel_moves
from .result import run_detailed
from .simple_model import SimpleInputs, run_simple, simple_scenario

__all__ = [
    "MODE_DETAILED", "MODE_SIMPLE", "ROLES",
    "Scenario", "ScenarioResult", "SimulationSummary", "finalize_summary",
    "OccurrenceRow", "derive_occurrences", "move_key",
    "PmsItem", "sl_revenue", "sl_revenue_per_item", "bco_revenue", "total_vessel_moves",
    "run_detailed", "SimpleInputs", "run_simple", "simple_scenario",
    "methodology", "overtime", "shares", "deals", "pricing",
]
