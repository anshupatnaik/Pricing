"""Full Storage (dwell x tariff) revenue — bottom-up, tier-based.

Per FULL_STORAGE_CALCULATION_GUIDE.md: a container's dwell days beyond a
tariff's free period are billed against tiered per-day rates. Revenue for one
(category, dwell_days) bucket = container_count x revenue for one container
with that many dwell days under that category's tariff.

Sources (see data/repository.py): the dwell histogram comes from Storage
Insights (category x dwell_days x container_count for a terminal + operator);
the tariff tiers come from Pricing.Customer_Rate_Sheets ('Full Storage -
Import/Export/Transshipment' activities), effective-sheet picked the same way
as BEM quay rates (engine.pricing.choose_rate_sheet).
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: A tier_end this high means "open-ended" (through the end of the container's dwell,
#: or — for the free-pool quantity axis — no upper bound on the excess). Chosen well
#: above any realistic dwell-day (observed up to ~1,371) or TEU-pool tier boundary,
#: so it can never collide with a real one.
UNBOUNDED_TIER_END = 10**7


@dataclass(frozen=True)
class StorageTariff:
    """One category's tariff: free days, then ordered (day_start, day_end, rate) tiers."""

    free_days: int
    tiers: list[tuple[int, int, float]] = field(default_factory=list)


@dataclass(frozen=True)
class DwellBucket:
    """One (category, dwell_days) bucket with its container count."""

    category: str
    dwell_days: int
    container_count: float


def build_tariff(tier_rows: list[tuple[int, int, float]]) -> StorageTariff:
    """Build a :class:`StorageTariff` from raw (tier_start, tier_end, rate) rows.

    A zero-rate row is the free period, not a billing tier — its end day becomes
    ``free_days`` (matching how Customer_Rate_Sheets encodes free time: a real
    tier row with ``Rate=0``, not a separate column). Every rate>0 row becomes a
    billing tier, sorted by start day.
    """
    free_days = 0
    tiers = []
    for start, end, rate in tier_rows:
        if rate == 0:
            free_days = max(free_days, end)
        else:
            tiers.append((start, end, rate))
    tiers.sort(key=lambda t: t[0])
    return StorageTariff(free_days=free_days, tiers=tiers)


def revenue_per_container(dwell_days: int, tariff: StorageTariff) -> float:
    """Billable revenue for ONE container with this many dwell days.

    Days at or under ``free_days`` are free. Each tier's rate applies to the
    days of the container's dwell that fall inside that tier (absolute day
    numbers, not relative to the free period); a tier ending at
    :data:`UNBOUNDED_TIER_END` runs through the end of the container's dwell.
    """
    if dwell_days <= tariff.free_days:
        return 0.0
    billable_start = tariff.free_days + 1
    revenue = 0.0
    for tier_start, tier_end, rate in tariff.tiers:
        end = tier_end if tier_end < UNBOUNDED_TIER_END else dwell_days
        overlap_start = max(tier_start, billable_start)
        overlap_end = min(end, dwell_days)
        if overlap_start <= overlap_end:
            revenue += (overlap_end - overlap_start + 1) * rate
    return revenue


#: Alias for pool-based (Empty Storage) charging: the same tier-crossing math as
#: :func:`revenue_per_container`, just against a different quantity axis — a
#: day's TEU occupancy above a free-pool allowance, instead of a container's
#: total dwell days above a free-days allowance. ``tariff.free_days`` doubles as
#: the pool size Y in this usage.
revenue_for_quantity = revenue_per_container


def pool_revenue(daily_occupancy: list[float], tariff: StorageTariff) -> float:
    """Total Empty Storage (free-pool) revenue across a period.

    ``daily_occupancy`` is one TEU figure per day (dwell time is irrelevant here
    — only how many empty TEU are physically at the terminal that day matters).
    Each day is charged independently against the pool tariff and summed.
    """
    return sum(revenue_for_quantity(q, tariff) for q in daily_occupancy)


def storage_revenue_by_category(
    buckets: list[DwellBucket], tariffs: dict[str, StorageTariff]
) -> dict[str, float]:
    """Total storage revenue per category = Sum(container_count x revenue_per_container).

    A bucket whose category has no tariff (e.g. no signed rate for that
    direction) contributes nothing — not an error, just unpriced volume.
    """
    out: dict[str, float] = {}
    for b in buckets:
        tariff = tariffs.get(b.category)
        if tariff is None:
            continue
        out[b.category] = out.get(b.category, 0.0) + b.container_count * revenue_per_container(
            b.dwell_days, tariff
        )
    return out


def total_storage_revenue(buckets: list[DwellBucket], tariffs: dict[str, StorageTariff]) -> float:
    """Sum of :func:`storage_revenue_by_category` across all categories."""
    return sum(storage_revenue_by_category(buckets, tariffs).values())
