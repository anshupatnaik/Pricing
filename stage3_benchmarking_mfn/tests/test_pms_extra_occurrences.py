"""Rail/Truck/OOG/Overtime occurrence derivation — vUSA PMS parity structure.

Covers the workbook 'Automatic Ocurrences' additions: Truck/Rail gate legs (XOR
carrier-mode rule), the single OOG surcharge line, and per-day-hour overtime
buckets. SQL shape is asserted directly; row->OccurrenceRow mapping is exercised
with a fake Dremio client (no live connection).
"""
from __future__ import annotations

from data import queries
from data.repository import MovesSimRepository
from engine.occurrences import OOG_ITEM, gate_key


# --- item keys ---------------------------------------------------------------
def test_gate_key_and_norm_length():
    assert gate_key("Rail", "Full", "40") == "Rail-Full-40"
    assert gate_key("Truck", "Empty", 20.0) == "Truck-Empty-20"


# --- SQL shape ---------------------------------------------------------------
def test_carrier_xor_sql_is_exclusive():
    sql = queries.sql_gate_leg_occurrences("T", [], [], "2025-01-01", "2025-12-31", "TRAIN")
    # exactly-one-leg (XOR) logic, not OR: a "=mode AND <>mode" pair each way
    assert "= 'TRAIN' AND" in sql and "<> 'TRAIN'" in sql
    assert " OR (" in sql
    assert "GROUP BY unit_freight_group, cont_length" in sql


def test_oog_sql_exact_match_single_total():
    sql = queries.sql_oog_occurrences("T", [], [], "2025-01-01", "2025-12-31")
    assert "= 'OOG'" in sql and "SUM(total_moves)" in sql
    assert "GROUP BY" not in sql  # single scalar total, not per-length


def test_overtime_sql_groups_by_indicator():
    sql = queries.sql_overtime_occurrences("T", [], [], "2025-01-01", "2025-12-31")
    assert "overtime_inidcator" in sql            # source column typo preserved
    assert "GROUP BY overtime_inidcator" in sql


# --- repository row -> OccurrenceRow mapping ---------------------------------
class _FakeClient:
    """Minimal DremioClient stand-in that dispatches on SQL content."""

    def query(self, sql):
        if "overtime_inidcator AS overtime_indicator" in sql:
            return (["overtime_indicator", "total_moves"],
                    [{"overtime_indicator": "Monday - 00:00-00:59", "total_moves": 10},
                     {"overtime_indicator": "Sunday - 12:00-12:59", "total_moves": 5}])
        if "= 'OOG'" in sql:
            return (["total_moves"], [{"total_moves": 30}])
        if "'TRUCK'" in sql:
            return (["unit_freight_group", "cont_length", "total_moves"],
                    [{"unit_freight_group": "Full", "cont_length": "40", "total_moves": 100}])
        if "'TRAIN'" in sql:
            return (["unit_freight_group", "cont_length", "total_moves"],
                    [{"unit_freight_group": "Empty", "cont_length": "20", "total_moves": 7}])
        if "GROUP BY unit_freight_group, event_type, cont_length" in sql:
            return (["unit_freight_group", "event_type", "cont_length", "total_moves"],
                    [{"unit_freight_group": "Full", "event_type": "Load",
                      "cont_length": "40", "total_moves": 50}])
        return ([], [])


def _occ():
    repo = MovesSimRepository(_FakeClient())
    return {o.item: o for o in repo.get_occurrences(
        "T", [], [], "2025-01-01", "2025-12-31",
        include_hazard=False, include_shiftings=False)}


def test_new_groups_labels_and_flags():
    by = _occ()
    assert by["Truck-Full-40"].group == "Truck Moves" and by["Truck-Full-40"].count == 100
    assert by["Rail-Empty-20"].group == "Rail Moves" and by["Rail-Empty-20"].count == 7
    assert by[OOG_ITEM].group == "Surcharge - OOG" and by[OOG_ITEM].count == 30
    assert by["Monday - 00:00-00:59"].group == "Overtime Vessel Moves"
    assert by["Sunday - 12:00-12:59"].count == 5
    # gate/OOG/overtime are landside/surcharge lines, not extra vessel moves
    for k in ("Truck-Full-40", "Rail-Empty-20", OOG_ITEM, "Monday - 00:00-00:59"):
        assert by[k].vessel_move is False
    # base gateway line still present and flagged as a vessel move
    assert by["Full-Load-40"].group == "Vessel Moves-Gateway" and by["Full-Load-40"].vessel_move


def test_annualized_equals_count_for_full_year():
    by = _occ()  # 2025-01-01..2025-12-31 == 365 days -> annualized == raw count
    assert round(by["Truck-Full-40"].annualized) == 100
    assert round(by[OOG_ITEM].annualized) == 30
