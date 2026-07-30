"""Closed-deal tracking: classify a chosen scenario vs CPI and measure upside.

A *deal* records one simulation's per-scenario total revenue plus which scenario
the customer actually closed on. Aggregated across deals, this answers: how many
closed at / above / below CPI, and what revenue upside was captured (chosen vs the
baseline/current scenario).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

AT_CPI = "at CPI"
ABOVE_CPI = "above CPI"
BELOW_CPI = "below CPI"
NO_CPI = "no CPI scenario"


@dataclass
class Deal:
    """One recorded, closed simulation."""

    customer: str
    terminal: str
    operator: str
    date_from: str
    date_to: str
    mode: str
    scenario_revenues: dict[str, float]      # scenario name -> total revenue
    chosen_scenario: str
    baseline_scenario: str
    cpi_scenario: str | None = None
    saved_at: str = ""                        # ISO timestamp (stamped by caller)
    notes: str = ""
    id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Deal":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


def classify_vs_cpi(deal: Deal, tol: float = 1e-6) -> str:
    """Whether the chosen scenario's revenue is at / above / below the CPI scenario."""
    if not deal.cpi_scenario or deal.cpi_scenario not in deal.scenario_revenues:
        return NO_CPI
    chosen = deal.scenario_revenues.get(deal.chosen_scenario)
    cpi = deal.scenario_revenues.get(deal.cpi_scenario)
    if chosen is None or cpi is None:
        return NO_CPI
    rel = tol * max(1.0, abs(cpi))
    if chosen > cpi + rel:
        return ABOVE_CPI
    if chosen < cpi - rel:
        return BELOW_CPI
    return AT_CPI


def upside(deal: Deal) -> float:
    """Chosen revenue minus the baseline (current) scenario revenue."""
    chosen = deal.scenario_revenues.get(deal.chosen_scenario, 0.0)
    base = deal.scenario_revenues.get(deal.baseline_scenario, 0.0)
    return (chosen or 0.0) - (base or 0.0)


def upside_vs_cpi(deal: Deal) -> float | None:
    """Chosen revenue minus the CPI scenario revenue (None if no CPI scenario)."""
    if not deal.cpi_scenario or deal.cpi_scenario not in deal.scenario_revenues:
        return None
    return (deal.scenario_revenues.get(deal.chosen_scenario, 0.0) or 0.0) - \
           (deal.scenario_revenues.get(deal.cpi_scenario, 0.0) or 0.0)


@dataclass
class DealAggregate:
    count: int = 0
    at_cpi: int = 0
    above_cpi: int = 0
    below_cpi: int = 0
    no_cpi: int = 0
    total_upside: float = 0.0
    total_chosen_revenue: float = 0.0
    rows: list = field(default_factory=list)   # per-deal enriched dicts


def aggregate(deals) -> DealAggregate:
    """Summarise a list of deals for the tracker view."""
    agg = DealAggregate()
    buckets = {AT_CPI: "at_cpi", ABOVE_CPI: "above_cpi", BELOW_CPI: "below_cpi", NO_CPI: "no_cpi"}
    for d in deals:
        cls = classify_vs_cpi(d)
        up = upside(d)
        agg.count += 1
        setattr(agg, buckets[cls], getattr(agg, buckets[cls]) + 1)
        agg.total_upside += up
        agg.total_chosen_revenue += d.scenario_revenues.get(d.chosen_scenario, 0.0) or 0.0
        agg.rows.append({
            "customer": d.customer, "terminal": d.terminal, "operator": d.operator,
            "chosen_scenario": d.chosen_scenario, "vs_CPI": cls,
            "chosen_revenue": d.scenario_revenues.get(d.chosen_scenario, 0.0),
            "upside_vs_current": up, "upside_vs_CPI": upside_vs_cpi(d),
            "saved_at": d.saved_at, "notes": d.notes,
        })
    return agg
