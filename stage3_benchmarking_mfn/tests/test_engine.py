"""Unit tests for the pure engine (no Dremio, no network)."""
from __future__ import annotations

import pytest

from engine import (
    PmsItem, Scenario, derive_occurrences, move_key, overtime, methodology,
    quay_revenue, run_detailed, sl_revenue, total_vessel_moves,
)
from engine.occurrences import annualize, hazard_key
from engine.simple_model import SimpleInputs, run_simple


# --- occurrences -------------------------------------------------------------
def test_move_key_normalises_length():
    assert move_key("Full", "Load", 40) == "Full-Load-40"
    assert move_key("Full", "Load", "40.0") == "Full-Load-40"


def test_derive_occurrences_sums_by_key():
    moves = [
        {"unit_freight_group": "Full", "event_type": "Load", "cont_length": 40, "total_moves": 10},
        {"unit_freight_group": "Full", "event_type": "Load", "cont_length": "40", "total_moves": 5},
        {"unit_freight_group": "Empty", "event_type": "Discharge", "cont_length": 20, "total_moves": 3},
    ]
    occ = {o.item: o.count for o in derive_occurrences(moves, date_from="45658", date_to="46022")}
    assert occ["Full-Load-40"] == 15
    assert occ["Empty-Discharge-20"] == 3


def test_hazard_occurrence_key_rounds_imdg():
    assert hazard_key("IMO", "3.1,8.0") == "IMO 3,8 Load/Discharge"
    moves = [{"unit_freight_group": "Full", "event_type": "Load", "cont_length": 40,
              "total_moves": 2, "imo_indicator": "IMO", "cargo_imdg_types": "3.1,8.0"}]
    occ = {o.item: o for o in derive_occurrences(moves)}
    assert occ["IMO 3,8 Load/Discharge"].count == 2
    assert occ["IMO 3,8 Load/Discharge"].vessel_move is False


def test_annualize():
    assert annualize(100, 365) == pytest.approx(100)
    assert annualize(100, 730) == pytest.approx(50)
    assert annualize(100, None) is None


# --- detailed (PMS) revenue --------------------------------------------------
def _items():
    return [
        PmsItem("G", "Full-Load-40", occurrences=17,
                rates={"Current": 69.36, "Floor": 60, "Target": 90}, bco_rate=400),
        PmsItem("G", "Empty-Discharge-20", occurrences=3,
                rates={"Current": 17.5, "Floor": 15, "Target": 30}, bco_rate=0),
    ]


def test_sl_revenue_occ_times_rate_over_roe():
    sl = sl_revenue(_items(), ["Current"], roe=1.0)
    assert sl["Current"] == pytest.approx(17 * 69.36 + 3 * 17.5)
    sl2 = sl_revenue(_items(), ["Current"], roe=2.0)
    assert sl2["Current"] == pytest.approx((17 * 69.36 + 3 * 17.5) / 2.0)


def test_run_detailed_result_and_deltas():
    scen = [Scenario("Current", "current"), Scenario("Floor", "floor"), Scenario("Target", "target")]
    s = run_detailed(_items(), scen, roe=1.0, var_cost_per_move=-32.0, baseline_name="Current")
    by = {r.name: r for r in s.scenarios}
    assert by["Current"].total_moves == 20  # vessel-move occurrences
    assert by["Current"].components["BCO"] == pytest.approx(17 * 400)
    # variable cost = -32 * 20 moves; contribution margin = total + var_cost
    assert by["Current"].variable_cost == pytest.approx(-640)
    assert by["Current"].contribution_margin == pytest.approx(by["Current"].total_revenue - 640)
    assert by["Current"].delta_total == 0
    assert by["Target"].delta_total > 0 and by["Floor"].delta_total < 0


def test_sl_revenue_per_item_sums_match_totals():
    from engine.revenue import sl_revenue, sl_revenue_per_item
    items = _items()
    rows = sl_revenue_per_item(items, ["Current", "Target"], roe=1.0)
    assert len(rows) == len(items)
    assert rows[0]["Item"] == "Full-Load-40" and rows[0]["Vessel Move?"] == "YES"
    totals = sl_revenue(items, ["Current", "Target"], roe=1.0)
    assert sum(r["Current"] for r in rows) == pytest.approx(totals["Current"])
    assert sum(r["Target"] for r in rows) == pytest.approx(totals["Target"])


def test_total_vessel_moves_excludes_non_vessel():
    items = _items() + [PmsItem("H", "IMO 3 Load/Discharge", occurrences=5,
                                rates={"Current": 10}, vessel_move=False)]
    assert total_vessel_moves(items) == 20


# --- blended overtime (average uplift % on quay revenue) ---------------------
def test_quay_revenue_restricted_to_gateway_and_restow():
    items = [
        PmsItem("Vessel Moves-Gateway", "Full-Load-40", occurrences=10, rates={"Current": 50.0}),
        PmsItem("Vessel Moves-Restow on board", "Restow on board-Full-20", occurrences=4,
                rates={"Current": 20.0}),
        PmsItem("Truck Moves", "Truck-Full-40", occurrences=100, rates={"Current": 30.0},
                vessel_move=False),
    ]
    rev = quay_revenue(items, ["Current"], roe=1.0)
    assert rev["Current"] == pytest.approx(10 * 50.0 + 4 * 20.0)  # Truck excluded from the base


def test_run_detailed_blended_overtime_adds_ot_component():
    items = [
        PmsItem("Vessel Moves-Gateway", "Full-Load-40", occurrences=10,
                rates={"Current": 50.0, "Floor": 40.0}),
        PmsItem("Truck Moves", "Truck-Full-40", occurrences=100,
                rates={"Current": 30.0, "Floor": 25.0}, vessel_move=False),
    ]
    scen = [Scenario("Current", "current"), Scenario("Floor", "floor")]
    s = run_detailed(items, scen, roe=1.0, baseline_name="Current", overtime_uplift_pct=0.20)
    cur = {r.name: r for r in s.scenarios}["Current"]
    assert cur.components["OT"] == pytest.approx(500.0 * 0.20)     # 20% of quay-only revenue
    assert cur.total_revenue == pytest.approx(500.0 + 3000.0 + 100.0)  # SL (quay+truck) + OT
    # default path (overtime_uplift_pct=None) never adds an OT component at all
    s2 = run_detailed(items, scen, roe=1.0, baseline_name="Current")
    assert "OT" not in s2.scenarios[0].components


def test_run_detailed_storage_revenue_is_per_scenario_and_additive():
    items = [PmsItem("Vessel Moves-Gateway", "Full-Load-40", occurrences=10, rates={"Current": 50.0})]
    scen = [Scenario("Current", "current"), Scenario("Floor", "floor")]
    storage_by_scenario = {"Current": 1000.0, "Floor": 800.0}  # e.g. Floor = looser free days
    s = run_detailed(items, scen, roe=1.0, baseline_name="Current",
                     storage_revenue=storage_by_scenario)
    by = {r.name: r for r in s.scenarios}
    assert by["Current"].components["Storage"] == 1000.0
    assert by["Floor"].components["Storage"] == 800.0
    assert by["Current"].total_revenue == pytest.approx(500.0 + 1000.0)  # SL + Storage
    # a scenario missing from the dict gets 0, not a crash
    s2 = run_detailed(items, scen, roe=1.0, baseline_name="Current",
                      storage_revenue={"Current": 1000.0})
    assert s2.scenarios[1].components["Storage"] == 0.0
    # default path (storage_revenue=None) never adds a Storage component at all
    s3 = run_detailed(items, scen, roe=1.0, baseline_name="Current")
    assert "Storage" not in s3.scenarios[0].components


def test_run_detailed_full_and_empty_storage_are_separate_components():
    items = [PmsItem("Vessel Moves-Gateway", "Full-Load-40", occurrences=10, rates={"Current": 50.0})]
    scen = [Scenario("Current", "current")]
    s = run_detailed(items, scen, roe=1.0, baseline_name="Current",
                     storage_revenue={"Current": 1000.0},
                     empty_storage_revenue={"Current": 300.0})
    cur = s.scenarios[0]
    assert cur.components["Storage"] == 1000.0
    assert cur.components["EmptyStorage"] == 300.0
    assert cur.total_revenue == pytest.approx(500.0 + 1000.0 + 300.0)  # SL + Storage + EmptyStorage
    # default path never adds an EmptyStorage component at all
    s2 = run_detailed(items, scen, roe=1.0, baseline_name="Current")
    assert "EmptyStorage" not in s2.scenarios[0].components


def test_run_detailed_reefer_is_its_own_component():
    items = [PmsItem("Vessel Moves-Gateway", "Full-Load-40", occurrences=10, rates={"Current": 50.0})]
    scen = [Scenario("Current", "current")]
    s = run_detailed(items, scen, roe=1.0, baseline_name="Current",
                     storage_revenue={"Current": 1000.0}, reefer_revenue={"Current": 400.0})
    cur = s.scenarios[0]
    assert cur.components["Reefer"] == 400.0
    assert cur.components["Storage"] == 1000.0
    assert cur.total_revenue == pytest.approx(500.0 + 1000.0 + 400.0)
    s2 = run_detailed(items, scen, roe=1.0, baseline_name="Current")
    assert "Reefer" not in s2.scenarios[0].components


# --- overtime ----------------------------------------------------------------
def test_overtime_average():
    assert overtime.average_uplift([0.2, 0.2, 0.0, 0.0, 0.2]) == pytest.approx(0.12)
    assert overtime.average_uplift([]) == 0.0
    assert overtime.average_uplift([0.2, "x", None, 0.4]) == pytest.approx(0.3)


# --- methodology -------------------------------------------------------------
def test_cpi_and_ordering():
    assert methodology.cpi_escalate(100, 0.017) == pytest.approx(101.7)
    ok, msgs = methodology.validate_ordering(
        {"F": {"x": 10}, "A": {"x": 12}, "T": {"x": 15}}, "F", "A", "T")
    assert ok and not msgs
    bad, msgs = methodology.validate_ordering(
        {"F": {"x": 20}, "A": {"x": 12}, "T": {"x": 15}}, "F", "A", "T")
    assert not bad and msgs


# --- edge cases --------------------------------------------------------------
def test_zero_volume_simple_no_crash():
    inp = SimpleInputs(volume=0, scenarios=[Scenario("A", "current")],
                       shares={"full_ld": 0.5}, rates={"full_ld": {"A": 100}})
    s = run_simple(inp)
    assert s.scenarios[0].total_revenue == 0
    assert s.scenarios[0].rpm is None  # no moves -> RPM undefined


def test_zero_baseline_delta_pct_none():
    scen = [Scenario("A", "current"), Scenario("B", "target")]
    items = [PmsItem("G", "x", occurrences=0, rates={"A": 0, "B": 5})]
    s = run_detailed(items, scen, baseline_name="A")
    b = {r.name: r for r in s.scenarios}["B"]
    assert b.delta_pct is None  # baseline revenue is 0
