"""Tests for TOS-key -> BEM-SKU matching, rate-sheet choice, and cycle basis."""
from __future__ import annotations

import pytest

from engine.pricing import (
    apply_basis, choose_rate_sheet, match_rate, parse_tos_key, rates_for_keys,
    parse_rate, oog_surcharge, overtime_rate, parse_overtime_indicator,
)


# --- key parsing -------------------------------------------------------------
def test_parse_gateway_key():
    a = parse_tos_key("Full-Discharge-20")
    assert a.category == "gateway" and a.freight == "Full" and a.direction == "Discharge"
    assert a.length == "20" and a.length_ft == "20 ft"


def test_parse_transhipment_and_restow():
    assert parse_tos_key("Transhipment-Full-40").category == "Transhipment"
    r = parse_tos_key("Restow via quay-Empty-45")
    assert r.category == "Restow via quay" and r.freight == "Empty" and r.length == "45"


def test_parse_gate_and_restow_on_board():
    g = parse_tos_key("Gate-Full-40")
    assert g.category == "Gate" and g.freight == "Full" and g.length == "40"
    rb = parse_tos_key("Restow on board-Empty-20")
    assert rb.category == "Restow on board" and rb.freight == "Empty"


def test_match_gate_to_gateway_cycle():
    sheet = [_row("S", "2026-01-01", "2026-12-31", activity="Gateway Cycle Move",
                  freight="Full", length="40 ft", rate=127.5)]
    assert match_rate(parse_tos_key("Gate-Full-40"), sheet)["Rate"] == 127.5


def test_parse_excludes_storage_and_bad_length():
    assert parse_tos_key("STRGE-Empty-20") is None      # storage excluded
    assert parse_tos_key("Full-Load-24") is None         # non-standard length excluded
    assert parse_tos_key("Transhipment-Empty-") is None  # blank length excluded
    assert parse_tos_key("") is None


# --- rate-sheet choice (effective today -> latest start; tie -> ambiguous) ----
def _row(sid, start, end, activity="Load or Discharge Move", freight="Full",
         length="20 ft", rate=100.0):
    return {"RatesheetID": sid, "RateSheetName": sid, "EffectiveStartDate": start,
            "EffectiveEndDate": end, "activity_name": activity, "Freight_Type": freight,
            "Container_Length": length, "Rate": rate, "currency": "EUR", "SKU": activity}


def test_choose_latest_start():
    rows = [_row("HQ", "2025-06-01", "2026-05-31", rate=120),
            _row("LOCAL", "2026-06-01", "2027-05-31", rate=130)]
    chosen, info = choose_rate_sheet(rows, today="2026-07-13")
    assert info["ratesheet_id"] == "LOCAL" and info["ambiguous"] is False
    assert chosen[0]["Rate"] == 130


def test_choose_ambiguous_on_tie():
    rows = [_row("HQ", "2026-06-01", "2027-05-31", rate=120),
            _row("LOCAL", "2026-06-01", "2027-05-31", rate=130)]
    _, info = choose_rate_sheet(rows, today="2026-07-13")
    assert info["ambiguous"] is True and len(info["candidates"]) == 2


def test_effective_filter_excludes_expired():
    rows = [_row("OLD", "2024-01-01", "2025-01-31", rate=99)]
    chosen, info = choose_rate_sheet(rows, today="2026-07-13")
    assert chosen == [] and info["ratesheet_id"] is None


# --- SKU matching + fallback -------------------------------------------------
def test_match_exact_then_blended():
    sheet = [_row("S", "2026-01-01", "2026-12-31", freight="Full", length="20 ft", rate=100),
             _row("S", "2026-01-01", "2026-12-31", freight="Full", length="Any", rate=95)]
    a = parse_tos_key("Full-Discharge-20")
    assert match_rate(a, sheet)["Rate"] == 100          # exact length wins
    a40 = parse_tos_key("Full-Discharge-40")
    assert match_rate(a40, sheet)["Rate"] == 95          # falls back to blended Any


def test_match_transhipment_activity():
    sheet = [_row("S", "2026-01-01", "2026-12-31", activity="Transshipment Move",
                  freight="Full", length="40 ft", rate=70)]
    assert match_rate(parse_tos_key("Transhipment-Full-40"), sheet)["Rate"] == 70
    assert match_rate(parse_tos_key("Full-Discharge-40"), sheet) is None  # no gateway activity


# --- cycle basis -------------------------------------------------------------
def test_apply_basis():
    assert apply_basis(100.0, "per_move") == 100.0
    assert apply_basis(100.0, "per_cycle") == 50.0


def test_rates_for_keys_with_cycle():
    sheet = [_row("S", "2026-01-01", "2026-12-31", activity="Transshipment Move",
                  freight="Full", length="20 ft", rate=80)]
    out = rates_for_keys(["Transhipment-Full-20", "STRGE-Empty-20"], sheet,
                         basis_by_category={"Transhipment": "per_cycle"})
    assert "STRGE-Empty-20" not in out                    # excluded
    assert out["Transhipment-Full-20"]["rate"] == 40.0    # 80 / 2 (per cycle)


def test_rates_for_keys_skips_surcharge_pseudo_keys():
    # OOG / overtime line labels are not TOS move keys -> never matched to base rates
    sheet = [_row("S", "2026-01-01", "2026-12-31")]
    out = rates_for_keys(["OOG with spreader or slings", "Monday - 00:00-00:59"], sheet)
    assert out == {}


# --- surcharge/overtime rate parsing -----------------------------------------
def test_parse_rate_percentage_and_fixed():
    assert parse_rate("200.00%") == ("percentage", 2.0)
    assert parse_rate("95%") == ("percentage", 0.95)
    assert parse_rate("150", "percentage") == ("percentage", 1.5)
    assert parse_rate("1029", "fixed") == ("fixed", 1029.0)
    assert parse_rate("387") == ("fixed", 387.0)
    for na in ("NA", "N/A", "On Request", "Surcharges", ""):
        assert parse_rate(na) == (None, None)


# --- OOG surcharge (on top of Load/Discharge) --------------------------------
def _sur(activity, rate, metric="percentage",
         name="OOG - Standard or Over height Spreader"):
    return {"Surcharge_name": name, "activity_name": activity,
            "Surcharge_Rate": rate, "Surcharge_Metric": metric, "currency": "EUR"}


def test_oog_percentage_on_ld():
    r = oog_surcharge([_sur("Load or Discharge Move", "200.00%")], base_ld_rate=100.0)
    assert r["rate"] == 200.0 and r["kind"] == "percentage"


def test_oog_prefers_ld_activity():
    rows = [_sur("Yard Move", "300%"), _sur("Load or Discharge Move", "200%")]
    assert oog_surcharge(rows, 100.0)["activity"] == "Load or Discharge Move"


def test_oog_fixed_ignores_base():
    r = oog_surcharge([_sur("Load or Discharge Move", "1029", "fixed")], base_ld_rate=999.0)
    assert r["rate"] == 1029.0 and r["kind"] == "fixed"


def test_oog_absent_or_on_request():
    assert oog_surcharge([], 100.0) is None
    assert oog_surcharge([_sur("Load or Discharge Move", "On Request", None)], 100.0) is None


# --- overtime (day/time-banded, on top of quay ops) --------------------------
def test_parse_overtime_indicator():
    assert parse_overtime_indicator("Monday - 00:00-00:59") == ("monday", 0)
    assert parse_overtime_indicator("Sunday - 14:00-14:59") == ("sunday", 14 * 60)
    assert parse_overtime_indicator("garbage") is None


def _ot(activity, sd, ed, st_, et, rate, metric="percentage", cat="Quay Operations"):
    return {"activity_name": activity, "start_day": sd, "end_day": ed, "start_time": st_,
            "end_time": et, "overtime_rate": rate, "overtime_metric": metric, "category": cat}


def test_overtime_weekday_band_and_daytime_gap():
    rows = [_ot("Load or Discharge Move", "Monday", "Friday", "00:00", "07:00", "75%")]
    assert overtime_rate("Monday - 03:00-03:59", rows, 100.0)["rate"] == 75.0
    assert overtime_rate("Monday - 10:00-10:59", rows, 100.0) is None  # daytime, no band


def test_overtime_midnight_wrap_band():
    rows = [_ot("Load or Discharge Move", "Monday", "Friday", "20:00", "08:00", "20%")]
    assert overtime_rate("Tuesday - 03:00-03:59", rows, 100.0)["rate"] == 20.0
    assert overtime_rate("Tuesday - 12:00-12:59", rows, 100.0) is None


def test_overtime_sunday_and_fixed():
    rows = [_ot("Load or Discharge Move", "Saturday", "Sunday", "00:00", "23:59", "387", "fixed")]
    assert overtime_rate("Sunday - 12:00-12:59", rows, 100.0)["rate"] == 387.0


def test_overtime_excludes_gate_category():
    rows = [_ot("Gate Move Rail", "Saturday", "Saturday", "08:00", "20:00",
                "1664.52", "fixed", "Gate Operations")]
    assert overtime_rate("Saturday - 12:00-12:59", rows, 100.0) is None


def test_overtime_category_fallback_when_no_ld_row():
    rows = [_ot("Hatch Cover Move", "Sunday", "Sunday", "00:00", "23:59", "90%")]
    assert overtime_rate("Sunday - 12:00-12:59", rows, 100.0)["rate"] == 90.0
