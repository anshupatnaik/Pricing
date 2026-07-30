"""Tests for shares, scenario %-derivation, rate-sheet parsing, and deal tracking."""
from __future__ import annotations

import pandas as pd
import pytest

from app.ratesheet import parse_rate_sheet
from engine.deals import ABOVE_CPI, AT_CPI, BELOW_CPI, Deal, aggregate, classify_vs_cpi, upside
from engine.methodology import derive_from_pct
from engine.shares import compute_shares


# --- shares (reproduce the manager's pivot) ----------------------------------
def test_shares_reproduce_pivot():
    rows = [
        {"category": "Import", "unit_freight_group": "Full", "total_moves": 8230},
        {"category": "Import", "unit_freight_group": "Empty", "total_moves": 172},
        {"category": "Export", "unit_freight_group": "Full", "total_moves": 2934},
        {"category": "Export", "unit_freight_group": "Empty", "total_moves": 205},
        {"category": "Transhipment", "unit_freight_group": "Full", "total_moves": 5747},
        {"category": "Transhipment", "unit_freight_group": "Empty", "total_moves": 32010},
        {"category": "Restow via quay", "unit_freight_group": "Full", "total_moves": 951},
        {"category": "Restow via quay", "unit_freight_group": "Empty", "total_moves": 542},
        {"category": "STRGE", "unit_freight_group": "Empty", "total_moves": 9999},  # excluded
    ]
    sh = compute_shares(rows, reefer_moves=709)
    assert sh["_top_moves"] == 50791
    assert sh["full_ld"] == pytest.approx(11164 / 50791, abs=1e-4)
    assert sh["empty_ld"] == pytest.approx(377 / 50791, abs=1e-4)
    assert sh["transhipment"] == pytest.approx(37757 / 50791, abs=1e-4)
    assert sh["shift"] == pytest.approx(1493 / 50791, abs=1e-4)
    assert sh["reefer"] == pytest.approx(709 / 50791, abs=1e-4)
    assert sh["gate_full"] == sh["full_ld"]


def test_shares_empty_is_safe():
    sh = compute_shares([], reefer_moves=0)
    assert sh["_top_moves"] == 0 and sh["transhipment"] == 0


# --- scenario %-derivation + override ----------------------------------------
def test_derive_from_pct_and_override():
    current = {"full_ld": 100.0, "gate_full": 50.0}
    floor = derive_from_pct(current, -0.05)
    assert floor["full_ld"] == pytest.approx(95.0)
    target = derive_from_pct(current, 0.10, overrides={"gate_full": 999.0})
    assert target["full_ld"] == pytest.approx(110.0)
    assert target["gate_full"] == 999.0  # override wins


# --- rate-sheet parsing ------------------------------------------------------
def test_parse_rate_sheet_fuzzy():
    df = pd.DataFrame({
        "Item": ["Load/disc Full", "Load/disc Empty", "Transhipment", "Shift",
                 "Gate Full", "Gate Empty", "Reefer plug-in"],
        "Rate": ["127.5", "106", "70", "64", "$64", "52.5", "39.5"],
    })
    rates = parse_rate_sheet(df, "Item", "Rate")
    assert rates["full_ld"] == pytest.approx(127.5)
    assert rates["transhipment"] == pytest.approx(70)
    assert rates["gate_empty"] == pytest.approx(52.5)
    assert rates["reefer"] == pytest.approx(39.5)


# --- deal tracking -----------------------------------------------------------
def _deal(chosen, revs, cpi="CPI"):
    return Deal(customer="C", terminal="T", operator="O", date_from="", date_to="",
                mode="simple", scenario_revenues=revs, chosen_scenario=chosen,
                baseline_scenario="Current", cpi_scenario=cpi)


def test_classify_and_upside():
    revs = {"Current": 100.0, "CPI": 110.0, "Target": 120.0, "Floor": 90.0}
    assert classify_vs_cpi(_deal("Target", revs)) == ABOVE_CPI
    assert classify_vs_cpi(_deal("CPI", revs)) == AT_CPI
    assert classify_vs_cpi(_deal("Floor", revs)) == BELOW_CPI
    assert upside(_deal("Target", revs)) == pytest.approx(20.0)  # vs Current


def test_aggregate_counts():
    revs = {"Current": 100.0, "CPI": 110.0, "Target": 120.0}
    agg = aggregate([_deal("Target", revs), _deal("CPI", revs), _deal("Current", revs)])
    assert agg.count == 3
    assert agg.above_cpi == 1 and agg.at_cpi == 1 and agg.below_cpi == 1
    assert agg.total_upside == pytest.approx(20.0 + 10.0 + 0.0)


def test_deal_roundtrip():
    d = _deal("Target", {"Current": 1.0, "Target": 2.0})
    assert Deal.from_dict(d.to_dict()).chosen_scenario == "Target"
