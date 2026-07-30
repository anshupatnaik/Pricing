"""Scenario roles + rate derivations (floor / anchor / target / CPI ...).

This is the ONE place that gives scenarios pricing meaning and derives one
scenario's rates from another. The revenue engines stay agnostic — they just
consume a rate-per-scenario. Semantics (revenue management):

* current / anchor - the rates we charge today; the comparison baseline.
* floor           - walk-away minimum acceptable rates.
* target          - aspirational rates management wants to achieve.
* competitor      - a benchmark line's rates (e.g. MFN reference).
* cpi             - anchor escalated by inflation: rate x (1 + cpi).
* closing         - the agreed closing rates.

Invariant (:func:`validate_ordering`): at every line item ``floor <= anchor <= target``.
"""
from __future__ import annotations

from .models import ROLE_ANCHOR, ROLE_FLOOR, ROLE_TARGET  # noqa: F401 (re-export)


def cpi_escalate(rate: float, cpi: float) -> float:
    """rate x (1 + cpi)."""
    return rate * (1.0 + cpi)


def apply_multiplier(rate: float, multiplier: float) -> float:
    return rate * multiplier


def apply_increment(rate: float, increment: float) -> float:
    return rate + increment


def derive_curve(base_rates: dict[str, float], *, multiplier=1.0, increment=0.0) -> dict[str, float]:
    """Derive a scenario's per-line rates from a base: ``base*mult + increment``."""
    return {line: r * multiplier + increment for line, r in base_rates.items()}


def derive_from_pct(
    current_rates: dict[str, float],
    pct: float,
    overrides: dict[str, float] | None = None,
) -> dict[str, float]:
    """Scenario rates from Current by a single %: ``current * (1 + pct)``.

    ``pct`` is a fraction (0.03 = +3%; use negative for a discount, e.g. a floor
    below current). ``overrides`` (per line) always win, so the manager can hand-
    set any rate. Lines absent from ``overrides`` are derived.
    """
    overrides = overrides or {}
    out = {}
    for line, r in current_rates.items():
        out[line] = overrides[line] if line in overrides and overrides[line] is not None \
            else r * (1.0 + pct)
    return out


def validate_ordering(
    rates_by_scenario: dict[str, dict[str, float]],
    floor: str,
    anchor: str,
    target: str,
) -> tuple[bool, list[str]]:
    """Check ``floor <= anchor <= target`` for each line item.

    ``rates_by_scenario`` maps scenario name -> {line: rate}. Missing scenarios
    are skipped. Returns ``(ok, messages)`` naming the first offending lines.
    """
    f = rates_by_scenario.get(floor)
    a = rates_by_scenario.get(anchor)
    t = rates_by_scenario.get(target)
    present = [x for x in (f, a, t) if x is not None]
    if len(present) < 2:
        return True, []
    lines = set.intersection(*(set(c) for c in present))
    messages: list[str] = []
    for line in sorted(lines):
        seq = []
        if f is not None:
            seq.append((floor, f[line]))
        if a is not None:
            seq.append((anchor, a[line]))
        if t is not None:
            seq.append((target, t[line]))
        for (an, av), (bn, bv) in zip(seq, seq[1:]):
            if av > bv + 1e-9:
                messages.append(f"{line}: {an} ({av:g}) > {bn} ({bv:g})")
    return (not messages), messages
