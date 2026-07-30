"""Pure storage-revenue simulation engine (no I/O, no network, no UI).

Faithful port of the "Full Storage Sim" workbook's VBA. See the package modules:
``models``, ``rates``, ``teu``, ``revenue``, ``reefer_additional``, ``methodology``.
"""
from __future__ import annotations

from .models import (
    CARGO_TYPES,
    METHODS,
    METHOD_CONTAINER,
    METHOD_TEU_ADVANCED,
    METHOD_TEU_SIMPLE,
    MAX_DAY,
    RawRow,
    ScenarioRevenue,
    SimulationReport,
)
from .rates import RateBlock, RateSchedule
from .revenue import build_report, row_revenue, run_simulation
from .reefer_additional import reefer_additional
from .teu import teu_factor
from . import methodology

__all__ = [
    "CARGO_TYPES",
    "METHODS",
    "METHOD_CONTAINER",
    "METHOD_TEU_SIMPLE",
    "METHOD_TEU_ADVANCED",
    "MAX_DAY",
    "RawRow",
    "ScenarioRevenue",
    "SimulationReport",
    "RateBlock",
    "RateSchedule",
    "build_report",
    "row_revenue",
    "run_simulation",
    "reefer_additional",
    "teu_factor",
    "methodology",
]
