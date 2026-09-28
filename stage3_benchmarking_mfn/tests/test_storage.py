"""Tests for Full Storage (dwell x tariff) revenue.

Tier numbers mirror FULL_STORAGE_CALCULATION_GUIDE.md's worked example
(Barcelona/Hapag-Lloyd Import: days 1-5 free, 6-7 @ 2.00, 8-14 @ 5.00, 15+ @
40.00 EUR/day) — the same tariff confirmed live in Pricing.Customer_Rate_Sheets.
"""
from __future__ import annotations

import pytest

from data import queries
from data.repository import MovesSimRepository, _parse_tier_row, _storage_category_from_activity
from engine.storage import (
    DwellBucket,
    StorageTariff,
    UNBOUNDED_TIER_END,
    build_tariff,
    pool_revenue,
    revenue_for_quantity,
    revenue_per_container,
    storage_revenue_by_category,
    total_storage_revenue,
)


# --- tariff construction -------------------------------------------------
def test_build_tariff_infers_free_days_from_zero_rate_tier():
    tariff = build_tariff([(1, 5, 0.0), (6, 7, 2.0), (8, 14, 5.0), (15, UNBOUNDED_TIER_END, 40.0)])
    assert tariff.free_days == 5
    assert tariff.tiers == [(6, 7, 2.0), (8, 14, 5.0), (15, UNBOUNDED_TIER_END, 40.0)]


def test_build_tariff_zero_tier_can_start_at_day_zero():
    # Barcelona/Hapag Export: TierStart=0 (BEM's convention), free through day 8
    tariff = build_tariff([(0, 8, 0.0), (9, 14, 5.0), (15, UNBOUNDED_TIER_END, 40.0)])
    assert tariff.free_days == 8


def test_build_tariff_no_free_tier_defaults_to_zero_free_days():
    tariff = build_tariff([(1, UNBOUNDED_TIER_END, 10.0)])
    assert tariff.free_days == 0


# --- per-container revenue -------------------------------------------------
_IMPORT_TARIFF = StorageTariff(
    free_days=5, tiers=[(6, 7, 2.0), (8, 14, 5.0), (15, UNBOUNDED_TIER_END, 40.0)]
)


def test_revenue_per_container_within_free_days_is_zero():
    assert revenue_per_container(3, _IMPORT_TARIFF) == 0.0
    assert revenue_per_container(5, _IMPORT_TARIFF) == 0.0  # exactly the last free day


def test_revenue_per_container_spans_multiple_tiers():
    assert revenue_per_container(7, _IMPORT_TARIFF) == pytest.approx(4.0)     # 2d @2.00
    assert revenue_per_container(14, _IMPORT_TARIFF) == pytest.approx(39.0)   # 2@2 + 7@5
    assert revenue_per_container(20, _IMPORT_TARIFF) == pytest.approx(279.0)  # +6@40


def test_revenue_per_container_unbounded_tier_runs_to_end_of_dwell():
    tariff = StorageTariff(free_days=0, tiers=[(1, UNBOUNDED_TIER_END, 10.0)])
    assert revenue_per_container(45, tariff) == pytest.approx(450.0)


# --- aggregation over a dwell histogram ------------------------------------
def test_storage_revenue_by_category_sums_container_count_times_rate():
    tariffs = {"IMPRT": _IMPORT_TARIFF}
    buckets = [
        DwellBucket("IMPRT", dwell_days=3, container_count=100),   # free -> 0
        DwellBucket("IMPRT", dwell_days=7, container_count=50),    # 4.0/container
        DwellBucket("IMPRT", dwell_days=14, container_count=10),   # 39.0/container
    ]
    expected = 50 * 4.0 + 10 * 39.0
    assert storage_revenue_by_category(buckets, tariffs)["IMPRT"] == pytest.approx(expected)
    assert total_storage_revenue(buckets, tariffs) == pytest.approx(expected)


def test_storage_revenue_skips_categories_with_no_tariff():
    buckets = [DwellBucket("TRSHP", dwell_days=30, container_count=5)]
    assert storage_revenue_by_category(buckets, {}) == {}
    assert total_storage_revenue(buckets, {}) == 0.0


# --- SQL shape --------------------------------------------------------------
def test_storage_dwell_sql_filters_raw_terminal_and_full_containers():
    sql = queries.sql_storage_dwell("Barcelona", ["HLC"], "2026-01-01", "2026-06-30")
    assert "UPPER(s.TerminalName) = UPPER('Barcelona')" in sql
    assert "IN ('HLC')" in sql
    assert "'FCL','LCL'" in sql
    assert "GROUP BY" in sql


def test_storage_tariff_sql_scopes_to_full_storage_and_active_status():
    sql = queries.sql_storage_tariffs("APM Terminals Barcelona", "HPL")
    assert "STORAGE SERVICES" in sql
    assert "Full Storage%" in sql
    assert "NOT IN ('REJECTED', 'DELETED', 'DRAFT')" in sql
    assert "RatesheetID" in sql and "EffectiveStartDate" in sql  # choose_rate_sheet's expected keys


# --- activity-name -> category -----------------------------------------
def test_storage_category_from_activity_name():
    assert _storage_category_from_activity("Full Storage - Import") == "IMPRT"
    assert _storage_category_from_activity("Full Storage - Export") == "EXPRT"
    assert _storage_category_from_activity("Full Storage - Transshipment") == "TRSHP"
    assert _storage_category_from_activity("Empty Storage") is None


# ============================================================================
# Empty Storage: Logic 1 — daily free-pool allowance (dwell time irrelevant;
# only how many TEU sit at the terminal on a given calendar day matters).
# Real tariff numbers below are Eimskip Denmark/Aarhus, confirmed live in
# Pricing.Customer_Rate_Sheets ('Empty Storage - Free Pool', TierName "No of
# Empty TUE's"): 0-780 TEU free, 781+ @ 6.2 DKK/TEU/day.
# ============================================================================
_POOL_TARIFF = StorageTariff(free_days=780, tiers=[(781, UNBOUNDED_TIER_END, 6.2)])


def test_revenue_for_quantity_is_the_same_tier_crossing_math():
    # a day's TEU occupancy plays the exact role dwell_days plays for Full Storage
    assert revenue_for_quantity is revenue_per_container
    assert revenue_for_quantity(500, _POOL_TARIFF) == 0.0            # within the pool
    assert revenue_for_quantity(780, _POOL_TARIFF) == 0.0             # exactly at the pool size
    assert revenue_for_quantity(800, _POOL_TARIFF) == pytest.approx(20 * 6.2)  # 20 TEU over


def test_pool_revenue_sums_independently_charged_days():
    # one container present 1000 days stays free throughout if the pool never fills —
    # dwell time plays no role at all in this model.
    daily_occupancy = [500, 780, 900, 900, 500]  # 5 days
    total = pool_revenue(daily_occupancy, _POOL_TARIFF)
    # only days 3 and 4 (900 TEU) are over the 780 pool: 120 TEU x 6.2 x 2 days
    assert total == pytest.approx(120 * 6.2 * 2)


def test_pool_revenue_supports_progressive_tiers_above_the_pool():
    # the user's illustrative 3-tier example: 0-1000 excess @ Z, 1000-2000 @ P, 2000+ @ R
    tariff = StorageTariff(free_days=0, tiers=[(1, 1000, 1.0), (1001, 2000, 2.0), (2001, UNBOUNDED_TIER_END, 3.0)])
    # 2500 TEU excess: 1000@1 + 1000@2 + 500@3 = 1000+2000+1500 = 4500
    assert revenue_for_quantity(2500, tariff) == pytest.approx(4500.0)


# --- tier-row parsing (handles the common flat non-tiered case) -----------
def test_parse_tier_row_defaults_missing_start_and_end():
    # 'Empty Storage - Beyond Free Pool' is usually one flat rate with no
    # TierStart/TierEnd at all (PriceType=FIXED) — must still parse.
    assert _parse_tier_row({"tier_start": None, "tier_end": None, "rate": 6.2}) == (0, UNBOUNDED_TIER_END, 6.2)


def test_parse_tier_row_parses_numeric_strings_incl_scientific_notation():
    # Dremio returns TierStart as a decimal string, sometimes '0E-18' for zero
    assert _parse_tier_row({"tier_start": "0E-18", "tier_end": "780.000000000000000000", "rate": 0.0}) == (0, 780, 0.0)


def test_parse_tier_row_skips_free_text_only_rows():
    # PriceType=FREE_TEXT rows carry no structured Rate — must be skipped, not
    # silently coerced to a rate=0.0 tier (which would look like "free forever").
    assert _parse_tier_row({"tier_start": None, "tier_end": None, "rate": None}) is None


# --- SQL shape ---------------------------------------------------------
def test_empty_dwell_daily_sql_filters_mty_and_period_overlap():
    sql = queries.sql_empty_dwell_daily("Barcelona", ["HLC"], "2026-01-01", "2026-06-30")
    assert "UNIT_FREIGHT_KIND = 'MTY'" in sql
    assert "Event_Start_Date <= '2026-06-30'" in sql
    assert "Event_END_Date >= '2026-01-01'" in sql
    assert "teu_per_container" in sql


def test_empty_pool_tariff_sql_scopes_to_both_pool_activities():
    sql = queries.sql_empty_pool_tariff("APM Terminals Barcelona", "HPL")
    assert "'Empty Storage - Free Pool', 'Empty Storage - Beyond Free Pool'" in sql
    assert "STORAGE SERVICES" in sql


def test_empty_storage_tariff_sql_scopes_to_plain_empty_storage():
    sql = queries.sql_empty_storage_tariff("APM Terminals Barcelona", "HPL")
    assert "ActivityName = 'Empty Storage'" in sql


# --- daily occupancy reconstruction (fake client, no live Dremio) --------
class _FakeEmptyDwellClient:
    """Two presence intervals: 100 TEU/day for Jan 1-3, 50 TEU/day for Jan 2-4
    (each teu_per_container x container_count already resolved to a flat TEU
    figure for the row) — overlapping days should sum."""

    def query(self, sql):
        return (["start_date", "end_date", "teu_per_container", "container_count"],
                [{"start_date": "2026-01-01", "end_date": "2026-01-03",
                  "teu_per_container": 1, "container_count": 100},
                 {"start_date": "2026-01-02", "end_date": "2026-01-04",
                  "teu_per_container": 1, "container_count": 50}])


def test_get_empty_daily_occupancy_expands_and_sums_overlapping_intervals():
    repo = MovesSimRepository(_FakeEmptyDwellClient())
    occ = repo.get_empty_daily_occupancy("Barcelona", ["HLC"], "2026-01-01", "2026-01-04")
    assert occ["2026-01-01"] == 100.0
    assert occ["2026-01-02"] == 150.0  # both intervals cover day 2
    assert occ["2026-01-03"] == 150.0
    assert occ["2026-01-04"] == 50.0


def test_get_empty_daily_occupancy_clips_to_the_requested_period():
    repo = MovesSimRepository(_FakeEmptyDwellClient())
    occ = repo.get_empty_daily_occupancy("Barcelona", ["HLC"], "2026-01-02", "2026-01-02")
    assert set(occ) == {"2026-01-02"}
    assert occ["2026-01-02"] == 150.0
