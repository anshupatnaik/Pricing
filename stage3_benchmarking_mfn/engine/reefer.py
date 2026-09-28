"""Reefer storage revenue — a flat daily service charge, no tiering.

Unlike Full/Empty Storage, the daily reefer rate never changes with dwell time
(the pricing manager's own model: "daily reefer charge is always fixed, i.e.
no tiered pricing"), so revenue reduces to ``rate x total reefer-container-days``
— computed from ``container_count x average dwell days`` rather than a per-day
histogram, which gives the identical total since the rate is flat throughout.

Two ways to price it:
  * **Bundled** (default) — one daily rate covers plug-in/plug-out, electricity,
    and monitoring together (BEM's ``Daily Reefer Service`` activity).
  * **Unbundled** (an option) — a one-time per-container plug-in/plug-out fee
    (``Reefer Plug-in or Unplug``) plus separate daily electricity
    (``Daily Reefer Service - Electricity Only``) and monitoring
    (``Daily Reefer Service - Monitoring Only``) rates.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReeferTariff:
    """Bundled: ``bundled_daily_rate`` covers plug-in/out + electricity + monitoring.
    Unbundled: ``plug_fee`` (one-time, per container) + separate daily
    ``electricity_daily`` / ``monitoring_daily`` rates."""

    bundled_daily_rate: float = 0.0
    unbundled: bool = False
    plug_fee: float = 0.0
    electricity_daily: float = 0.0
    monitoring_daily: float = 0.0

    @property
    def daily_rate(self) -> float:
        """The rate charged for every day of dwell (electricity + monitoring
        when unbundled; the single bundled rate otherwise) — never the
        one-time plug fee, which :func:`reefer_revenue` adds separately."""
        return (self.electricity_daily + self.monitoring_daily) if self.unbundled else self.bundled_daily_rate


def reefer_revenue(container_count: float, avg_dwell_days: float, tariff: ReeferTariff) -> float:
    """Total reefer revenue: daily charge x total container-days, plus the
    one-time plug fee per container when unbundled (bundled mode already
    folds an equivalent plug cost into the single daily rate)."""
    revenue = tariff.daily_rate * avg_dwell_days * container_count
    if tariff.unbundled:
        revenue += tariff.plug_fee * container_count
    return revenue
