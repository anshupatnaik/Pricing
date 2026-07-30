"""Parameterized SQL builders for the storage simulator.

Ports the Power Query M source (reference/power_query.m) to the Dremio REST
client used elsewhere in this repo. The single source table is::

    "APMT-BEATS"."Global"."insights_and_visualizations".
        "Storage Insights - Power BI"."GBL_Storage_Excel_Simulator"

The four cargo streams are the same table with different boolean filters. We
GROUP BY the fields the revenue engine actually needs
(unit_category_fixed, container_length, dwell_days) and SUM container_count;
this is equivalent to the workbook (revenue is linear in count and independent
of month) but returns far fewer rows.

All identifiers are pre-quoted; string parameters are escaped by doubling single
quotes (``_q``). Prefer running these via ``--sql-file`` or the Python client to
avoid PowerShell quote-mangling (see dremio_connect/README.md).
"""
from __future__ import annotations

from engine.models import CARGO_DRY, CARGO_HAZARDOUS, CARGO_OOG, CARGO_REEFER

TABLE = (
    '"APMT-BEATS"."Global"."insights_and_visualizations".'
    '"Storage Insights - Power BI"."GBL_Storage_Excel_Simulator"'
)

# Boolean filters per cargo stream (verbatim from the M queries).
CARGO_FILTERS: dict[str, str] = {
    CARGO_DRY: "unit_is_oog = '0' AND cargo_is_hazardous = '0' AND unit_requires_power = '0'",
    CARGO_REEFER: "unit_requires_power = '1' AND cargo_is_hazardous = '0'",
    CARGO_HAZARDOUS: "unit_is_oog = '0' AND cargo_is_hazardous = '1'",
    CARGO_OOG: "unit_requires_power = '0' AND unit_is_oog = '1' AND cargo_is_hazardous = '0'",
}


def _q(value: str) -> str:
    """Escape a string for safe use inside a single-quoted SQL literal."""
    return str(value).replace("'", "''")


def _operator_filter(operators) -> str:
    ops = [o for o in (operators or []) if o]
    if not ops:
        return ""
    joined = "', '".join(_q(o) for o in ops)
    return f"  AND container_operator IN ('{joined}')\n"


def sql_raw(cargo_type: str, terminal: str, operators, date_from: str, date_to: str) -> str:
    """Aggregated occurrence rows for one cargo stream, ready for the engine.

    ``operators`` may be empty/None to include all operators. Dates are
    'YYYY-MM-DD' strings.
    """
    if cargo_type not in CARGO_FILTERS:
        raise ValueError(f"Unknown cargo type: {cargo_type!r}")
    return (
        "SELECT unit_category_fixed, container_length, dwell_days,\n"
        "       SUM(container_count) AS container_count\n"
        f"FROM {TABLE}\n"
        f"WHERE terminalname = '{_q(terminal)}'\n"
        f"  AND month_date >= '{_q(date_from)}'\n"
        f"  AND month_date <= '{_q(date_to)}'\n"
        "  AND freight_kind = 'Full'\n"
        "  AND unit_category_fixed <> 'Restow'\n"
        f"  AND {CARGO_FILTERS[cargo_type]}\n"
        f"{_operator_filter(operators)}"
        "GROUP BY unit_category_fixed, container_length, dwell_days"
    )


def sql_terminals() -> str:
    """Distinct terminal names for the picker (enables any-terminal support)."""
    return (
        "SELECT DISTINCT terminalname\n"
        f"FROM {TABLE}\n"
        "WHERE terminalname IS NOT NULL AND terminalname <> ''\n"
        "ORDER BY terminalname"
    )


def sql_operators(terminal: str | None = None) -> str:
    """Distinct operator codes, optionally scoped to a terminal."""
    where = "WHERE container_operator IS NOT NULL AND container_operator <> ''\n"
    if terminal:
        where += f"  AND terminalname = '{_q(terminal)}'\n"
    return (
        "SELECT DISTINCT container_operator\n"
        f"FROM {TABLE}\n"
        f"{where}"
        "ORDER BY container_operator"
    )
