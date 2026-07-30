"""Parity: the detailed engine reproduces the PMS 'SL Revenue per Ocurrence' row 39.

The shipped PMS workbook is a clean template (occurrences all 0), so this asserts
the engine's occ x rate / RoE totals match the workbook's cached row-39 totals
(structurally exact; numeric coverage of non-zero data is via the unit tests and
the live DAL smoke test noted in the README).
"""
from __future__ import annotations

import pytest

from engine.revenue import PmsItem, sl_revenue


def test_pms_row39_parity(pms_fixture):
    names = pms_fixture["scenario_names"]
    roe = pms_fixture["roe"] or 1.0
    items = [
        PmsItem(
            group="", item=it["item"], occurrences=it["occ"],
            rates={names[i]: it["rates"][i] for i in range(len(names))},
        )
        for it in pms_fixture["items"]
    ]
    got = sl_revenue(items, names, roe)
    expected = pms_fixture["expected_rev_row39"]
    for i, name in enumerate(names):
        if expected[i] is None:
            continue
        assert got[name] == pytest.approx(expected[i], abs=0.5)


def test_pms_formula_on_synthetic_occurrences(pms_fixture):
    # Same items but force occurrences=100 to prove the formula scales linearly.
    names = pms_fixture["scenario_names"]
    items = [
        PmsItem(group="", item=it["item"], occurrences=100.0,
                rates={names[i]: it["rates"][i] for i in range(len(names))})
        for it in pms_fixture["items"]
    ]
    got = sl_revenue(items, names, roe=1.0)
    # column F ("Current Rates") == 100 * sum(current rate over items)
    manual = 100.0 * sum(it["rates"][0] for it in pms_fixture["items"])
    assert got[names[0]] == pytest.approx(manual)
