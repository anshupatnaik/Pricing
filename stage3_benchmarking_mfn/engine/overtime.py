"""Overtime uplift handling.

Two ways the manager supplies overtime (both feed a single uplift % per scenario,
applied to quay/vessel-move revenue in the simple model):

* an **average uplift %** typed directly, or
* a **detailed hourly weekday/weekend grid** (the workbook's ``Overtime`` tab),
  which is averaged down to that % (mean of the hourly factors, matching row 170).
"""
from __future__ import annotations


def average_uplift(hourly_values) -> float:
    """Mean of an hourly overtime-factor list/iterable (0 if empty).

    Non-numeric entries are ignored, matching an AVERAGE over a mixed column.
    """
    nums = []
    for v in hourly_values:
        try:
            nums.append(float(v))
        except (TypeError, ValueError):
            continue
    return sum(nums) / len(nums) if nums else 0.0


def uplift_from_grid(grid) -> dict[str, float]:
    """Average each operator/scenario column of a grid dict.

    ``grid`` maps scenario/operator name -> iterable of hourly factors. Returns
    scenario -> average uplift %.
    """
    return {name: average_uplift(vals) for name, vals in grid.items()}
