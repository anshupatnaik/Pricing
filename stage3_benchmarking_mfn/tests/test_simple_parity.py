"""Parity: the simple model reproduces the Hapag 'Vado HMM (2)' workbook exactly."""
from __future__ import annotations

import pytest

from engine.models import Scenario
from engine.simple_model import SimpleInputs, run_simple

# scenario -> rate-column letter in the workbook
COLS = {"Maersk": "B", "Hapag": "C", "HMM Floor": "D"}
# rate line -> workbook row
RATE_ROWS = {
    "full_ld": 15, "empty_ld": 16, "transhipment": 18, "shift": 17,
    "gate_full": 12, "gate_empty": 13, "reefer": 20,
}


def _build_inputs(V):
    def g(ref):
        x = V.get(ref)
        return float(x) if x not in (None, "") else 0.0

    def per(row):
        return {name: g(f"{col}{row}") for name, col in COLS.items()}

    scenarios = [
        Scenario("Maersk", "competitor"),
        Scenario("Hapag", "current"),
        Scenario("HMM Floor", "floor"),
    ]
    rates = {line: per(row) for line, row in RATE_ROWS.items()}
    shares = {
        "full_ld": g("B3"), "empty_ld": g("B2"), "transhipment": g("B4"), "shift": g("B5"),
        "reefer": g("B6"), "reefer_dwell": g("B7"),
        "gate_full": g("E3"), "gate_empty": g("E4"), "oog": g("E5"), "imo": g("E6"),
    }
    return SimpleInputs(
        volume=g("B1"), scenarios=scenarios, shares=shares, rates=rates,
        overtime_pct=per(23), rebate_rate=per(27), oog_mult=per(31), imo_mult=per(32),
        baseline_name="Hapag",
    )


def test_hapag_vado_parity(hapag_fixture):
    V = hapag_fixture["vado_values"]

    def g(ref):
        x = V.get(ref)
        return float(x) if x not in (None, "") else 0.0

    summary = run_simple(_build_inputs(V))
    by_name = {r.name: r for r in summary.scenarios}
    # (scenario, column-letter) expected cells
    expect = {
        "Maersk": {"Quay": g("L6"), "Total": g("L18"), "TAR": g("L21"), "RPM": g("L22")},
        "Hapag": {"Quay": g("M6"), "Total": g("M18"), "TAR": g("M21"), "RPM": g("M22")},
        "HMM Floor": {"Quay": g("N6"), "Total": g("N18"), "TAR": g("N21"), "RPM": g("N22")},
    }
    for name, exp in expect.items():
        r = by_name[name]
        assert r.components["Quay"] == pytest.approx(exp["Quay"], abs=0.5)
        assert r.components["Total"] == pytest.approx(exp["Total"], abs=0.5)
        assert r.components["Total after rebate"] == pytest.approx(exp["TAR"], abs=0.5)
        assert r.rpm == pytest.approx(exp["RPM"], abs=1e-4)


def test_baseline_delta_is_zero(hapag_fixture):
    summary = run_simple(_build_inputs(hapag_fixture["vado_values"]))
    base = [r for r in summary.scenarios if r.name == summary.baseline_name][0]
    assert base.delta_total == 0
