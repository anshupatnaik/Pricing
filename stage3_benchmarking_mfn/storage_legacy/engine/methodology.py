"""Pricing methodology: floor / anchor / target scenario roles + benchmark_mfn.

The production workbook exposes a *Baseline* column plus eight free-form
*Scenario* columns. This module is the ONE place that gives those columns
business meaning as named pricing roles, so the rest of the engine stays
agnostic (a scenario is just a named rate curve).

Semantics (revenue-management standard):
  * baseline  - the current effective storage-rate schedule ("what we charge now").
  * anchor    - the reference schedule a negotiation opens from (defaults to baseline).
  * floor     - the walk-away minimum acceptable schedule.
  * target    - the aspirational schedule management wants to achieve.
  * benchmark_mfn - an external "most-favoured-nation" reference schedule that a
    target is calibrated against (e.g. the best rate offered to a comparable line).

The multipliers below are PLACEHOLDER starting points for *prefilling* a
scenario curve the pricing manager then edits; replace them with the desired
house methodology. All edits to pricing-role logic belong in this file only.

Invariant checked by :func:`validate_ordering`: at every storage day
``floor <= anchor <= target``.
"""
from __future__ import annotations

from dataclasses import dataclass

FLOOR = "floor"
ANCHOR = "anchor"
TARGET = "target"
BASELINE = "baseline"
CUSTOM = "custom"
ROLES = (BASELINE, FLOOR, ANCHOR, TARGET, CUSTOM)


@dataclass(frozen=True)
class RoleDefinition:
    """How to prefill a role's curve from a reference curve."""

    role: str
    reference: str      # "baseline" or "benchmark_mfn"
    multiplier: float
    note: str


DEFAULT_ROLE_DEFS: dict[str, RoleDefinition] = {
    FLOOR: RoleDefinition(FLOOR, BASELINE, 0.85, "PLACEHOLDER: floor = 85% of baseline (walk-away minimum)."),
    ANCHOR: RoleDefinition(ANCHOR, BASELINE, 1.00, "Anchor = current effective (baseline) schedule."),
    TARGET: RoleDefinition(TARGET, "benchmark_mfn", 1.00, "PLACEHOLDER: target = benchmark_mfn (falls back to +15% of baseline)."),
}


def prefill_curve(
    baseline_days: dict[int, float],
    benchmark_mfn_days: dict[int, float] | None = None,
    role_defs: dict[str, RoleDefinition] | None = None,
) -> dict[str, dict[int, float]]:
    """Prefill floor/anchor/target day-curves from a baseline (+ optional MFN).

    ``baseline_days`` and ``benchmark_mfn_days`` map storage day -> rate for a
    single category. Returns ``{role: {day: rate}}``. When a role references
    ``benchmark_mfn`` but none is supplied, it falls back to the baseline scaled
    by a sensible default so the manager still gets a starting curve.
    """
    role_defs = role_defs or DEFAULT_ROLE_DEFS
    out: dict[str, dict[int, float]] = {}
    for role, d in role_defs.items():
        if d.reference == "benchmark_mfn" and benchmark_mfn_days:
            ref = benchmark_mfn_days
            mult = d.multiplier
        elif d.reference == "benchmark_mfn":
            # No MFN reference given: fall back to baseline +15%.
            ref = baseline_days
            mult = 1.15
        else:
            ref = baseline_days
            mult = d.multiplier
        out[role] = {day: ref.get(day, 0.0) * mult for day in baseline_days}
    return out


def validate_ordering(curves: dict[str, dict[int, float]]) -> tuple[bool, list[str]]:
    """Check ``floor <= anchor <= target`` at every shared storage day.

    ``curves`` maps role -> {day: rate}. Roles not present are skipped. Returns
    ``(ok, messages)`` where messages name the first offending days.
    """
    floor = curves.get(FLOOR)
    anchor = curves.get(ANCHOR)
    target = curves.get(TARGET)
    present = [c for c in (floor, anchor, target) if c is not None]
    if len(present) < 2:
        return True, []
    days = sorted(set.intersection(*(set(c) for c in present)))
    messages: list[str] = []
    for day in days:
        seq = []
        if floor is not None:
            seq.append((FLOOR, floor[day]))
        if anchor is not None:
            seq.append((ANCHOR, anchor[day]))
        if target is not None:
            seq.append((TARGET, target[day]))
        for (a_name, a_val), (b_name, b_val) in zip(seq, seq[1:]):
            if a_val > b_val + 1e-9:
                messages.append(
                    f"Day {day}: {a_name} ({a_val:g}) > {b_name} ({b_val:g})"
                )
    return (not messages), messages
