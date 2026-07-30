"""Simple (Hapag "Vado HMM (2)") share-based revenue model.

Faithful port of the tab's build-up (validated to the cent against the workbook):

    quay      = volume * Σ(rate_line * share_line)     over full/empty L/D, transhipment, shift
    gate      = volume * (gate_full*share + gate_empty*share)
    reefer    = reefer_rate * (volume * reefer_share) * reefer_dwell
    imo/oog   = volume * share * surcharge_mult * full_LD_rate
    overtime  = quay * overtime_pct
    total     = quay + gate + reefer + overtime + imo + oog
    rebate    = rebate_rate * full_LD_share * volume
    total_after_rebate = total - rebate
    (+ optional pasted storage and empty-pool totals)
    RPM       = total_after_rebate / volume

Rates/shares/percentages are supplied per scenario; the CPI / floor / target
derivations live in engine.methodology.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import MODE_SIMPLE, Scenario, ScenarioResult, finalize_summary


@dataclass(frozen=True)
class SimpleInputs:
    """All inputs for the simple model. ``rates`` etc. are keyed by scenario name."""

    volume: float
    scenarios: list[Scenario]
    shares: dict[str, float]                      # full_ld, empty_ld, transhipment, shift,
                                                  # gate_full, gate_empty, reefer, reefer_dwell, oog, imo
    rates: dict[str, dict[str, float]]            # line -> {scenario: rate}
    overtime_pct: dict[str, float] = field(default_factory=dict)   # scenario -> pct
    rebate_rate: dict[str, float] = field(default_factory=dict)    # scenario -> per-full-move rate
    oog_mult: dict[str, float] = field(default_factory=dict)       # scenario -> surcharge multiplier
    imo_mult: dict[str, float] = field(default_factory=dict)
    storage: dict[str, float] = field(default_factory=dict)        # scenario -> pasted total
    empty_pool: dict[str, float] = field(default_factory=dict)     # scenario -> pasted total
    baseline_name: str | None = None

    def rate(self, line: str, scenario: str) -> float:
        return float(self.rates.get(line, {}).get(scenario, 0.0) or 0.0)

    def share(self, key: str) -> float:
        return float(self.shares.get(key, 0.0) or 0.0)


# Quay/gate move lines: (rate line key, share key)
_MOVE_LINES = [
    ("full_ld", "full_ld"),
    ("empty_ld", "empty_ld"),
    ("transhipment", "transhipment"),
    ("shift", "shift"),
]
_GATE_LINES = [
    ("gate_full", "gate_full"),
    ("gate_empty", "gate_empty"),
]


def simple_scenario(inp: SimpleInputs, s: str, role: str) -> ScenarioResult:
    """Compute one scenario's revenue breakdown (pre-delta)."""
    vol = inp.volume
    quay = vol * sum(inp.rate(line, s) * inp.share(sh) for line, sh in _MOVE_LINES)
    gate = vol * sum(inp.rate(line, s) * inp.share(sh) for line, sh in _GATE_LINES)
    reefer = inp.rate("reefer", s) * (vol * inp.share("reefer")) * inp.share("reefer_dwell")
    full_rate = inp.rate("full_ld", s)
    imo = vol * inp.share("imo") * float(inp.imo_mult.get(s, 0.0) or 0.0) * full_rate
    oog = vol * inp.share("oog") * float(inp.oog_mult.get(s, 0.0) or 0.0) * full_rate
    overtime = quay * float(inp.overtime_pct.get(s, 0.0) or 0.0)
    total = quay + gate + reefer + overtime + imo + oog
    rebate = float(inp.rebate_rate.get(s, 0.0) or 0.0) * inp.share("full_ld") * vol
    total_after_rebate = total - rebate
    storage = float(inp.storage.get(s, 0.0) or 0.0)
    empty = float(inp.empty_pool.get(s, 0.0) or 0.0)
    total_revenue = total_after_rebate + storage + empty
    components = {
        "Quay": quay, "Gate": gate, "Reefer": reefer, "Overtime": overtime,
        "IMO": imo, "OOG": oog, "Total": total, "Rebate": -rebate,
        "Total after rebate": total_after_rebate, "Storage": storage, "Empty pool": empty,
    }
    return ScenarioResult(
        name=s, role=role, total_revenue=total_revenue, total_moves=vol, components=components
    )


def run_simple(inp: SimpleInputs):
    """Run the simple model across all scenarios -> SimulationSummary."""
    roles = {sc.name: sc.role for sc in inp.scenarios}
    results = [simple_scenario(inp, sc.name, sc.role) for sc in inp.scenarios]
    baseline = inp.baseline_name or (inp.scenarios[0].name if inp.scenarios else "")
    return finalize_summary(MODE_SIMPLE, results, baseline)
