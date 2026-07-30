"""Rate schedules and the cumulative day-rate summation.

A rate schedule mirrors the ``E:P`` block of a workbook simulation sheet:
storage days ``Day 0 .. Day 45`` grouped into *blocks*. In the basic
simulations a block is one ``unit_category_fixed`` value (Import / Export /
Transshipment); in the reefer-additional sheet a block is a charge kind
(Electricity / Other Charges). Each block carries a *type* (the sheet's G
column) that drives the over-45 fallback (see ``engine.revenue``).

Each day holds one rate per column: index 0 is the baseline, 1..N are the
scenarios.

Cumulative revenue for a container that dwelled ``d`` days (VBA-faithful)::

    d <= 45 : sum(rate[day] for day in 0..d)                    # inclusive
    d  > 45 : sum(rate[day] for day in 0..45) + (d-45)*rate[45]
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import MAX_DAY


@dataclass(frozen=True)
class RateBlock:
    """One category/charge-kind block of daily rates.

    ``days`` maps a storage day (0..45) to a tuple of rates, one per column
    (baseline followed by each scenario).
    """

    key: str
    type_: str
    days: dict[int, tuple[float, ...]]

    @property
    def n_cols(self) -> int:
        return len(next(iter(self.days.values()))) if self.days else 0

    def has_day(self, day: int) -> bool:
        return day in self.days

    def rate(self, day: int, col: int) -> float:
        return self.days[day][col]

    def cumulative(self, dwell_days: int, col: int) -> float:
        """Sum of daily rates for a container dwelling ``dwell_days`` days.

        Applies the over-45 flat extrapolation at the Day-45 rate.
        """
        if dwell_days < 0:
            return 0.0
        capped = min(dwell_days, MAX_DAY)
        base = sum(self.days[d][col] for d in range(0, capped + 1) if d in self.days)
        if dwell_days > MAX_DAY and MAX_DAY in self.days:
            base += (dwell_days - MAX_DAY) * self.days[MAX_DAY][col]
        return base


@dataclass(frozen=True)
class RateSchedule:
    """A collection of rate blocks plus the scenario count."""

    blocks: dict[str, RateBlock]
    n_scenarios: int

    @property
    def n_cols(self) -> int:
        return self.n_scenarios + 1

    def block(self, key: str) -> RateBlock | None:
        return self.blocks.get(key)

    @classmethod
    def from_rows(cls, rows, n_scenarios: int = 8) -> "RateSchedule":
        """Build a schedule from ``(day, key, type_, rates)`` tuples.

        ``rates`` must be a sequence of length ``n_scenarios + 1`` (baseline
        first). Rows sharing a ``key`` are merged into one block; the block's
        ``type_`` is taken from the first row seen for that key.
        """
        blocks: dict[str, dict] = {}
        types: dict[str, str] = {}
        for day, key, type_, rates in rows:
            rates = tuple(float(r) for r in rates)
            if len(rates) != n_scenarios + 1:
                raise ValueError(
                    f"row for {key!r} day {day} has {len(rates)} rates, "
                    f"expected {n_scenarios + 1}"
                )
            blocks.setdefault(key, {})[int(day)] = rates
            types.setdefault(key, type_)
        return cls(
            blocks={k: RateBlock(k, types[k], d) for k, d in blocks.items()},
            n_scenarios=n_scenarios,
        )

    @classmethod
    def from_category_map(cls, mapping, type_="", n_scenarios: int = 8) -> "RateSchedule":
        """Convenience builder from ``{category: {day: [baseline, s1..sN]}}``.

        Useful in tests. ``type_`` is applied to every block.
        """
        rows = []
        for key, day_rates in mapping.items():
            for day, rates in day_rates.items():
                rows.append((day, key, type_, rates))
        return cls.from_rows(rows, n_scenarios=n_scenarios)
