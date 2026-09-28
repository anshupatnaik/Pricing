"""Tests for reefer storage revenue — flat daily rate, no tiering.

Tariff numbers mirror what's live in Pricing.Customer_Rate_Sheets for
Barcelona/Hapag-Lloyd: bundled 'Daily Reefer Service' = 51.25 EUR/day,
one-time 'Reefer Plug-in or Unplug' = 12.00 EUR.
"""
from __future__ import annotations

import pytest

from data import queries
from engine.reefer import ReeferTariff, reefer_revenue


# --- bundled (default) ------------------------------------------------------
def test_bundled_revenue_is_flat_rate_times_container_days():
    tariff = ReeferTariff(bundled_daily_rate=51.25)
    # 28,790 reefer containers, avg dwell 9.18 days (real Barcelona/HLC figures)
    assert reefer_revenue(28790, 9.18, tariff) == pytest.approx(51.25 * 9.18 * 28790)


def test_bundled_daily_rate_property_ignores_unbundled_fields():
    tariff = ReeferTariff(bundled_daily_rate=50.0, plug_fee=999, electricity_daily=999, monitoring_daily=999)
    assert tariff.daily_rate == 50.0


# --- unbundled ---------------------------------------------------------------
def test_unbundled_revenue_splits_one_time_and_daily_charges():
    tariff = ReeferTariff(unbundled=True, plug_fee=12.0, electricity_daily=30.0, monitoring_daily=5.0)
    # daily_rate = electricity + monitoring only (plug fee is one-time, added separately)
    assert tariff.daily_rate == pytest.approx(35.0)
    revenue = reefer_revenue(container_count=100, avg_dwell_days=10.0, tariff=tariff)
    expected = 35.0 * 10.0 * 100 + 12.0 * 100  # daily charge x container-days + one-time plug fee
    assert revenue == pytest.approx(expected)


def test_unbundled_with_zero_containers_is_zero():
    tariff = ReeferTariff(unbundled=True, plug_fee=12.0, electricity_daily=30.0, monitoring_daily=5.0)
    assert reefer_revenue(0, 10.0, tariff) == 0.0


# --- SQL shape ---------------------------------------------------------
def test_reefer_volume_sql_filters_power_flag_not_dwell_tiers():
    sql = queries.sql_reefer_volume("Barcelona", ["HLC"], "2026-01-01", "2026-06-30")
    assert "UNIT_REQUIRES_POWER = '1'" in sql
    assert "container_days" in sql  # weighted-average input, not a naive AVG()
    assert "AVG(" not in sql


def test_reefer_tariff_sql_covers_all_four_activities():
    sql = queries.sql_reefer_tariff("APM Terminals Barcelona", "HPL")
    for activity in ("Daily Reefer Service", "Daily Reefer Service - Electricity Only",
                     "Daily Reefer Service - Monitoring Only", "Reefer Plug-in or Unplug"):
        assert activity in sql
