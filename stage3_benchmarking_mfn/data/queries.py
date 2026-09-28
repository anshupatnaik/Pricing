"""Parameterized SQL for the SL revenue simulator (ports the Power Query M).

Sources (schema ``"Vessel Moves Insights - Power BI"``), reached via the same
Dremio REST client as the rest of the repo:
  * GBL_moves_simulator          - vessel moves (occurrence source)
  * GBL_service_list             - distinct terminal/operator/service (pickers)
  * GBL_Shift_on_board_simulator - restow / shift-on-board moves

Moves aggregation matches the workbook's occurrence key
(``unit_freight_group-event_type-cont_length``) by grouping and summing
``total_moves``. String parameters are escaped by doubling single quotes.
"""
from __future__ import annotations

_SCHEMA = '"APMT-BEATS"."Global"."insights_and_visualizations"."Vessel Moves Insights - Power BI"'
TABLE_MOVES = f'{_SCHEMA}."GBL_moves_simulator"'
TABLE_SERVICE_LIST = f'{_SCHEMA}."GBL_service_list"'
TABLE_SHIFTINGS = f'{_SCHEMA}."GBL_Shift_on_board_simulator"'


def _q(value) -> str:
    return str(value).replace("'", "''")


def _in_filter(column: str, values) -> str:
    vals = [v for v in (values or []) if v not in (None, "")]
    if not vals:
        return ""
    joined = "', '".join(_q(v) for v in vals)
    return f"  AND {column} IN ('{joined}')\n"


def _moves_where(terminal, operators, services, date_from, date_to,
                 op_col="unit_container_operator_id", svc_col="service_name") -> str:
    return (
        f"WHERE terminalname = '{_q(terminal)}'\n"
        f"  AND event_date >= '{_q(date_from)}'\n"
        f"  AND event_date <= '{_q(date_to)}'\n"
        "  AND event_year > 2017\n"
        f"{_in_filter(op_col, operators)}"
        f"{_in_filter(svc_col, services)}"
    )


def sql_moves_occurrences(terminal, operators, services, date_from, date_to) -> str:
    """Aggregated occurrence rows: freight/event/length + summed total_moves."""
    return (
        "SELECT unit_freight_group, event_type, cont_length,\n"
        "       SUM(total_moves) AS total_moves\n"
        f"FROM {TABLE_MOVES}\n"
        f"{_moves_where(terminal, operators, services, date_from, date_to)}"
        "GROUP BY unit_freight_group, event_type, cont_length"
    )


def _carrier_xor(mode: str) -> str:
    """Workbook gate rule: EXACTLY ONE of the IB/OB visit legs uses ``mode``.

    Ports the vUSA PMS SUMIFS pair
    ``SUMIFS(J=mode, K<>mode) + SUMIFS(J<>mode, K=mode)``: a both-legs-``mode``
    row is excluded, and a TRUCK-one-leg / TRAIN-other-leg row counts once for
    TRUCK and once for TRAIN. COALESCE treats a blank leg as ``<> mode`` (matching
    Excel's ``"<>"`` criteria on empty cells).
    """
    mode = str(mode).upper()
    ob = "COALESCE(UPPER(TRIM(actual_ob_visit_carrier_mode)), '')"
    ib = "COALESCE(UPPER(TRIM(actual_ib_visit_carrier_mode)), '')"
    return (f"(({ob} = '{mode}' AND {ib} <> '{mode}')\n"
            f"       OR ({ob} <> '{mode}' AND {ib} = '{mode}'))")


def sql_gate_leg_occurrences(terminal, operators, services, date_from, date_to, mode) -> str:
    """Gate-move occurrences for a carrier ``mode`` by freight group + length.

    ``mode='TRUCK'`` -> Truck Moves, ``mode='TRAIN'`` -> Rail Moves. Uses the
    workbook XOR rule (:func:`_carrier_xor`) so both-legs-``mode`` rows are dropped.
    """
    return (
        "SELECT unit_freight_group, cont_length, SUM(total_moves) AS total_moves\n"
        f"FROM {TABLE_MOVES}\n"
        f"{_moves_where(terminal, operators, services, date_from, date_to)}"
        f"  AND {_carrier_xor(mode)}\n"
        "GROUP BY unit_freight_group, cont_length"
    )


def sql_oog_occurrences(terminal, operators, services, date_from, date_to) -> str:
    """OOG occurrences: total moves flagged ``oog_indicator='OOG'`` (single line,
    all freight/length), matching the workbook ``SUMIF(E,"OOG",U)`` (item 41)."""
    return (
        "SELECT SUM(total_moves) AS total_moves\n"
        f"FROM {TABLE_MOVES}\n"
        f"{_moves_where(terminal, operators, services, date_from, date_to)}"
        "  AND UPPER(TRIM(oog_indicator)) = 'OOG'"
    )


def sql_overtime_occurrences(terminal, operators, services, date_from, date_to) -> str:
    """Overtime occurrences by day-hour bucket, matching the workbook
    ``SUMIF(V,<bucket>,U)`` (items 59+, e.g. 'Monday - 00:00-00:59').

    NB: the Dremio/TOS column is misspelled ``overtime_inidcator``; it already
    holds ``'<day_of_week> - <event_hour>'``.
    """
    return (
        "SELECT overtime_inidcator AS overtime_indicator,\n"
        "       SUM(total_moves) AS total_moves\n"
        f"FROM {TABLE_MOVES}\n"
        f"{_moves_where(terminal, operators, services, date_from, date_to)}"
        "  AND overtime_inidcator IS NOT NULL AND overtime_inidcator <> ''\n"
        "GROUP BY overtime_inidcator"
    )


def sql_moves_hazard(terminal, operators, services, date_from, date_to) -> str:
    """Aggregated hazardous-surcharge occurrences (imo + imdg + moves)."""
    return (
        "SELECT imo_indicator, cargo_imdg_types, SUM(total_moves) AS total_moves\n"
        f"FROM {TABLE_MOVES}\n"
        f"{_moves_where(terminal, operators, services, date_from, date_to)}"
        "  AND imo_indicator IS NOT NULL AND imo_indicator <> ''\n"
        "GROUP BY imo_indicator, cargo_imdg_types"
    )


def sql_category_breakdown(terminal, operators, services, date_from, date_to) -> str:
    """Moves by category + freight group (for simple-mode share computation)."""
    return (
        "SELECT category, unit_freight_group, SUM(total_moves) AS total_moves\n"
        f"FROM {TABLE_MOVES}\n"
        f"{_moves_where(terminal, operators, services, date_from, date_to)}"
        "GROUP BY category, unit_freight_group"
    )


def sql_indicator_total(terminal, operators, services, date_from, date_to, indicator: str) -> str:
    """Total moves where a cross-cut indicator is set (reefer/oog/imo).

    ``indicator`` selects the predicate: 'reefer' -> reefer_indicator='Live Reefers';
    'oog'/'imo' -> the respective indicator column is non-empty.
    """
    if indicator == "reefer":
        pred = "reefer_indicator = 'Live Reefers'"
    elif indicator == "oog":
        pred = "oog_indicator IS NOT NULL AND oog_indicator <> ''"
    elif indicator == "imo":
        pred = "imo_indicator IS NOT NULL AND imo_indicator <> ''"
    else:
        raise ValueError(f"Unknown indicator: {indicator!r}")
    return (
        "SELECT SUM(total_moves) AS total_moves\n"
        f"FROM {TABLE_MOVES}\n"
        f"{_moves_where(terminal, operators, services, date_from, date_to)}"
        f"  AND {pred}"
    )


def sql_shiftings(terminal, operators, services, date_from, date_to) -> str:
    """Restow / shift-on-board moves (different operator/service column names)."""
    return (
        "SELECT unit_freight_group, event_type, cont_length,\n"
        "       SUM(total_moves) AS total_moves\n"
        f"FROM {TABLE_SHIFTINGS}\n"
        f"{_moves_where(terminal, operators, services, date_from, date_to, op_col='container_operator_id', svc_col='actual_ob_service_name')}"
        "GROUP BY unit_freight_group, event_type, cont_length"
    )


_PAW = '"APMT-BEATS"."Global"."insights_and_visualizations"."Pricing Automation Workflow"'
TABLE_BEM = f'{_PAW}."Benchmarking"."BEM_Pricing_Base"'
TABLE_TERMINAL_MAP = f'{_PAW}."Lookups"."Terminal_mapping"'   # cols: Raw_Terminal, Std_Terminal, ...
TABLE_CUSTOMER_MAP = f'{_PAW}."Lookups"."Customer_mapping"'   # cols: Operator, Standard_Operator_Code, ...
TABLE_COST = f'{_PAW}."Cost"."Cost_OS"'                        # cols: Terminal_SalesForce, Metric, "Value", actual_date
TABLE_SURCHARGE = f'{_PAW}."Benchmarking"."BEM_Pricing_Surcharge"'  # OOG etc. (percentage of a referenced activity)
TABLE_OVERTIME = f'{_PAW}."Benchmarking"."BEM_Pricing_Overtime"'    # day/time-banded overtime surcharge

_INSIGHTS = '"APMT-BEATS"."Global"."insights_and_visualizations"'
# Container-level dwell detail (Full Storage volume side); raw TerminalName/CONTAINER_OPERATOR
# match the TOS moves/shiftings convention (filter on the raw selected terminal/operator codes,
# not Std_Terminal) — this is operational volume data, not a BEM pricing table.
TABLE_STORAGE_INSIGHTS = f'{_INSIGHTS}."Storage Insights - Power BI"."GBL_TF_CONTAINER_STORAGE_VW"'
# Signed/accepted customer storage tariffs (Full Storage tier side); standardized via the
# Lookups like BEM, since Customer here holds full descriptive names ("Hapag-Lloyd").
TABLE_CUSTOMER_RATE_SHEETS = f'{_INSIGHTS}."Pricing"."Customer_Rate_Sheets"'

# All cross-source joins standardize via the Lookups using UPPER(TRIM(...)) so
# terminal/customer names line up (future CIE platform consistency).


def _ci(col: str, value: str) -> str:
    """Case-insensitive, trimmed equality predicate."""
    return f"UPPER(TRIM({col})) = UPPER(TRIM('{_q(value)}'))"


def _ci_in(col: str, values) -> str:
    vals = [v for v in (values or []) if v not in (None, "")]
    if not vals:
        return ""
    joined = "', '".join(_q(str(v).strip().upper()) for v in vals)
    return f"  AND UPPER(TRIM({col})) IN ('{joined}')\n"


# Terminal_mapping column names flip-flop upstream between two schemas; the
# repository detects the live names and passes them in. Aliases stabilize output.
TERM_RAW_CANDIDATES = ("Raw_Terminal", "terminalName")
TERM_STD_CANDIDATES = ("Std_Terminal", "Standard_Terminal")


def sql_standard_terminal(tos_terminal: str, term_raw="Raw_Terminal", term_std="Std_Terminal") -> str:
    """Std terminal for a raw terminal name (Terminal_mapping, UPPER/TRIM join)."""
    return (
        f"SELECT {term_std} AS std_terminal\n"
        f"FROM {TABLE_TERMINAL_MAP}\n"
        f"WHERE {_ci(term_raw, tos_terminal)}\n"
        "LIMIT 1"
    )


def sql_standard_operator(operator: str) -> str:
    """Standard_Operator_Code for a raw operator code/name (Customer_mapping)."""
    return (
        "SELECT Standard_Operator_Code AS sc, Standard_Operator_Name AS sn\n"
        f"FROM {TABLE_CUSTOMER_MAP}\n"
        f"WHERE {_ci('Operator', operator)}\n"
        "LIMIT 1"
    )


def sql_pricing_operators(standard_terminal: str, term_raw="Raw_Terminal", term_std="Std_Terminal") -> str:
    """Standard operators (code+name) that have quay rates at a standard terminal.

    BEM.Customer is standardized via Customer_mapping so the picker shows the same
    operator identity as the moves side.
    """
    return (
        "SELECT DISTINCT cm.Standard_Operator_Code AS sc, cm.Standard_Operator_Name AS sn\n"
        f"FROM {TABLE_BEM} b\n"
        f"JOIN {TABLE_TERMINAL_MAP} t ON UPPER(TRIM(t.{term_raw})) = UPPER(TRIM(b.Pricing_Terminal))\n"
        f"JOIN {TABLE_CUSTOMER_MAP} cm ON UPPER(TRIM(cm.Operator)) = UPPER(TRIM(b.Customer))\n"
        f"WHERE {_ci(f't.{term_std}', standard_terminal)}\n"
        "  AND b.category_name = 'Quay Operations'\n"
        "ORDER BY cm.Standard_Operator_Name"
    )


def sql_bem_quay_rates(standard_terminal, standard_operator, activities,
                       term_raw="Raw_Terminal", term_std="Std_Terminal") -> str:
    """Quay-move BEM rows for a standard terminal + standard operator code.

    Both terminal and customer are standardized through the Lookups with
    UPPER(TRIM()). Effective-today + tie-break are applied in Python.
    """
    acts = "', '".join(_q(a) for a in activities)
    return (
        "SELECT b.SKU, b.activity_name, b.Freight_Type, b.Container_Length, b.Direction,\n"
        "       b.Rate, b.currency, b.EffectiveStartDate, b.EffectiveEndDate,\n"
        "       b.RatesheetID, b.RateSheetName, b.Customer, b.Pricing_Terminal\n"
        f"FROM {TABLE_BEM} b\n"
        f"JOIN {TABLE_TERMINAL_MAP} t ON UPPER(TRIM(t.{term_raw})) = UPPER(TRIM(b.Pricing_Terminal))\n"
        f"JOIN {TABLE_CUSTOMER_MAP} cm ON UPPER(TRIM(cm.Operator)) = UPPER(TRIM(b.Customer))\n"
        f"WHERE {_ci(f't.{term_std}', standard_terminal)}\n"
        f"  AND {_ci('cm.Standard_Operator_Code', standard_operator)}\n"
        "  AND b.category_name = 'Quay Operations'\n"
        f"  AND b.activity_name IN ('{acts}')"
    )


def sql_bem_gate_rates(standard_terminal, standard_operator, activities,
                       term_raw="Raw_Terminal", term_std="Std_Terminal") -> str:
    """Gate-move (Truck/Rail) BEM rows for a standard terminal + standard operator code.

    Same standardization as :func:`sql_bem_quay_rates`, scoped to
    ``category_name = 'Gate Operations'`` — a separate BEM category from quay ops,
    covering the landside Truck/Rail legs (``Gate Move Truck`` / ``Gate Move Rail``).
    """
    acts = "', '".join(_q(a) for a in activities)
    return (
        "SELECT b.SKU, b.activity_name, b.Freight_Type, b.Container_Length, b.Direction,\n"
        "       b.Rate, b.currency, b.EffectiveStartDate, b.EffectiveEndDate,\n"
        "       b.RatesheetID, b.RateSheetName, b.Customer, b.Pricing_Terminal\n"
        f"FROM {TABLE_BEM} b\n"
        f"JOIN {TABLE_TERMINAL_MAP} t ON UPPER(TRIM(t.{term_raw})) = UPPER(TRIM(b.Pricing_Terminal))\n"
        f"JOIN {TABLE_CUSTOMER_MAP} cm ON UPPER(TRIM(cm.Operator)) = UPPER(TRIM(b.Customer))\n"
        f"WHERE {_ci(f't.{term_std}', standard_terminal)}\n"
        f"  AND {_ci('cm.Standard_Operator_Code', standard_operator)}\n"
        "  AND b.category_name = 'Gate Operations'\n"
        f"  AND b.activity_name IN ('{acts}')"
    )


def sql_bem_surcharge_rates(standard_terminal, standard_operator,
                            term_raw="Raw_Terminal", term_std="Std_Terminal") -> str:
    """Surcharge BEM rows (OOG etc.) for a standard terminal + operator.

    Standardized like :func:`sql_bem_quay_rates`. Column aliases match the shape
    :func:`engine.pricing.choose_rate_sheet` expects (RatesheetID / RateSheetName /
    EffectiveStartDate / EffectiveEndDate), so the effective-sheet pick is reused.
    The OOG standard-spreader row is selected in Python.
    """
    return (
        "SELECT b.ActivityName AS activity_name, b.Surcharge_name, b.Surcharge_Rate,\n"
        "       b.Surcharge_Metric, b.Category, b.UoM, b.Currency AS currency,\n"
        "       b.EffectiveStartDate, b.EffectiveEndDate, b.RatesheetID, b.RateSheetName\n"
        f"FROM {TABLE_SURCHARGE} b\n"
        f"JOIN {TABLE_TERMINAL_MAP} t ON UPPER(TRIM(t.{term_raw})) = UPPER(TRIM(b.Pricing_Terminal))\n"
        f"JOIN {TABLE_CUSTOMER_MAP} cm ON UPPER(TRIM(cm.Operator)) = UPPER(TRIM(b.Customer))\n"
        f"WHERE {_ci(f't.{term_std}', standard_terminal)}\n"
        f"  AND {_ci('cm.Standard_Operator_Code', standard_operator)}"
    )


def sql_bem_overtime_rates(standard_terminal, standard_operator,
                           term_raw="Raw_Terminal", term_std="Std_Terminal") -> str:
    """Overtime BEM rows (activity x day-band x time-band) for a terminal + operator.

    Aliases the day/time/rate columns and the effective-date/ratesheet columns so
    both :func:`engine.pricing.choose_rate_sheet` and
    :func:`engine.pricing.overtime_rate` can consume the rows directly.
    """
    return (
        "SELECT b.ActivityName AS activity_name, b.overtime_name,\n"
        "       b.Surcharge_overtime_startDay AS start_day, b.Surcharge_overtime_endDay AS end_day,\n"
        "       b.Surcharge_overtime_startTime AS start_time, b.Surcharge_overtime_endTime AS end_time,\n"
        "       b.Surcharge_overtime_rate AS overtime_rate, b.overtime_rate_metric AS overtime_metric,\n"
        "       b.Surcharge_overtime_holidayType AS holiday_type, b.CategoryName AS category,\n"
        "       b.Referenced_Activity_Currency AS currency,\n"
        "       b.RatesheetID, b.ratesheetname AS RateSheetName,\n"
        "       b.ratesheet_effective_start AS EffectiveStartDate,\n"
        "       b.ratesheet_effective_end AS EffectiveEndDate\n"
        f"FROM {TABLE_OVERTIME} b\n"
        f"JOIN {TABLE_TERMINAL_MAP} t ON UPPER(TRIM(t.{term_raw})) = UPPER(TRIM(b.pricing_terminal))\n"
        f"JOIN {TABLE_CUSTOMER_MAP} cm ON UPPER(TRIM(cm.Operator)) = UPPER(TRIM(b.Customer))\n"
        f"WHERE {_ci(f't.{term_std}', standard_terminal)}\n"
        f"  AND {_ci('cm.Standard_Operator_Code', standard_operator)}"
    )


_STORAGE_CATEGORY_CASE = (
    "CASE "
    "WHEN s.UNIT_CATEGORY = 'STRGE' AND s.ACTUAL_IB_VISIT_CARRIER_MODE IN ('BARGE','TRAIN','TRUCK') "
    "AND s.ACTUAL_OB_VISIT_CARRIER_MODE = 'VESSEL' THEN 'EXPRT' "
    "WHEN s.UNIT_CATEGORY = 'STRGE' AND s.ACTUAL_IB_VISIT_CARRIER_MODE = 'VESSEL' "
    "AND s.ACTUAL_OB_VISIT_CARRIER_MODE IN ('BARGE','TRAIN','TRUCK') THEN 'IMPRT' "
    "WHEN s.UNIT_CATEGORY = 'STRGE' AND s.ACTUAL_IB_VISIT_CARRIER_MODE = 'VESSEL' "
    "AND s.ACTUAL_OB_VISIT_CARRIER_MODE = 'VESSEL' THEN 'TRSHP' "
    "ELSE s.UNIT_CATEGORY END"
)


def sql_storage_dwell(terminal, operators, date_from, date_to) -> str:
    """Full-container dwell histogram (category x dwell_days x container_count).

    Filtered on the raw selected terminal + operator codes, same convention as
    the moves/shiftings volume queries (Storage Insights is operational data,
    not a BEM pricing table, so it doesn't go through the Std_Terminal Lookups
    join). 'STRGE' rows are re-derived into Import/Export/Transshipment from
    carrier mode, mirroring agents/full_storage_roy's dwell-histogram pull;
    Full containers only (FCL/LCL) — Empty Storage isn't priced by this query.
    """
    return (
        f"SELECT {_STORAGE_CATEGORY_CASE} AS category, s.DWELL_DAYS AS dwell_days, "
        "SUM(s.Container_Count) AS container_count\n"
        f"FROM {TABLE_STORAGE_INSIGHTS} s\n"
        f"WHERE UPPER(s.TerminalName) = UPPER('{_q(terminal)}')\n"
        f"  AND s.Event_Start_Date >= '{_q(date_from)}'\n"
        f"  AND s.Event_Start_Date <= '{_q(date_to)}'\n"
        "  AND s.UNIT_FREIGHT_KIND IN ('FCL','LCL')\n"
        f"{_in_filter('s.CONTAINER_OPERATOR', operators)}"
        f"GROUP BY {_STORAGE_CATEGORY_CASE}, s.DWELL_DAYS"
    )


def sql_empty_storage_dwell(terminal, operators, date_from, date_to) -> str:
    """Empty-container dwell histogram (dwell_days x container_count) — the
    volume side of Empty Storage's Logic 2 (dwell-day tariff, same shape as
    Full Storage's, no Import/Export/Transshipment split since 'Empty Storage'
    is one activity regardless of direction)."""
    return (
        "SELECT s.DWELL_DAYS AS dwell_days, SUM(s.Container_Count) AS container_count\n"
        f"FROM {TABLE_STORAGE_INSIGHTS} s\n"
        f"WHERE UPPER(s.TerminalName) = UPPER('{_q(terminal)}')\n"
        f"  AND s.Event_Start_Date >= '{_q(date_from)}'\n"
        f"  AND s.Event_Start_Date <= '{_q(date_to)}'\n"
        "  AND s.UNIT_FREIGHT_KIND = 'MTY'\n"
        f"{_in_filter('s.CONTAINER_OPERATOR', operators)}"
        "GROUP BY s.DWELL_DAYS"
    )


def sql_storage_tariffs(standard_terminal, standard_operator,
                        term_raw="Raw_Terminal", term_std="Std_Terminal") -> str:
    """Full Storage tariff tiers (Import/Export/Transshipment) for a standard
    terminal + standard operator code, from Pricing.Customer_Rate_Sheets.

    Standardized like :func:`sql_bem_quay_rates`; column aliases match what
    :func:`engine.pricing.choose_rate_sheet` expects, so the same effective-
    sheet pick (latest start, tie -> ambiguous) is reused.
    """
    return (
        "SELECT rs.ActivityName AS activity_name, rs.TierStart AS tier_start, "
        "rs.TierEnd AS tier_end, rs.Rate AS rate, rs.Currency AS currency,\n"
        "       rs.RateSheetID AS RatesheetID, rs.RateSheetName, "
        "rs.EffectiveStartDate, rs.EffectiveEndDate\n"
        f"FROM {TABLE_CUSTOMER_RATE_SHEETS} rs\n"
        f"JOIN {TABLE_TERMINAL_MAP} t ON UPPER(TRIM(t.{term_raw})) = UPPER(TRIM(rs.Terminal))\n"
        f"JOIN {TABLE_CUSTOMER_MAP} cm ON UPPER(TRIM(cm.Operator)) = UPPER(TRIM(rs.Customer))\n"
        f"WHERE {_ci(f't.{term_std}', standard_terminal)}\n"
        f"  AND {_ci('cm.Standard_Operator_Code', standard_operator)}\n"
        "  AND UPPER(rs.CategoryName) = 'STORAGE SERVICES'\n"
        "  AND rs.ActivityName LIKE 'Full Storage%'\n"
        "  AND rs.RateSheetStatus NOT IN ('REJECTED', 'DELETED', 'DRAFT')"
    )


_TEU_PER_CONTAINER_CASE = "CASE WHEN POSITION('40' IN UPPER(s.CONTAINER_NOMINAL_LENGTH)) > 0 THEN 2 ELSE 1 END"


def sql_empty_dwell_daily(terminal, operators, date_from, date_to) -> str:
    """Empty-container presence intervals (start date, end date, TEU/container,
    container_count) overlapping the period — the input to a day-by-day TEU
    occupancy reconstruction (dwell time itself is irrelevant to the free-pool
    model; only how many TEU are physically present on each calendar day is).

    Same raw terminal/operator convention as :func:`sql_storage_dwell`.
    """
    return (
        f"SELECT s.Event_Start_Date AS start_date, s.Event_END_Date AS end_date, "
        f"{_TEU_PER_CONTAINER_CASE} AS teu_per_container, "
        "SUM(s.Container_Count) AS container_count\n"
        f"FROM {TABLE_STORAGE_INSIGHTS} s\n"
        f"WHERE UPPER(s.TerminalName) = UPPER('{_q(terminal)}')\n"
        "  AND s.UNIT_FREIGHT_KIND = 'MTY'\n"
        f"  AND s.Event_Start_Date <= '{_q(date_to)}'\n"
        f"  AND s.Event_END_Date >= '{_q(date_from)}'\n"
        f"{_in_filter('s.CONTAINER_OPERATOR', operators)}"
        f"GROUP BY s.Event_Start_Date, s.Event_END_Date, {_TEU_PER_CONTAINER_CASE}"
    )


def sql_empty_pool_tariff(standard_terminal, standard_operator,
                          term_raw="Raw_Terminal", term_std="Std_Terminal") -> str:
    """Empty Storage free-pool tariff (pool size Y + the tiered/flat rate beyond
    it) for a standard terminal + operator, from Pricing.Customer_Rate_Sheets.

    Two activities carry this: 'Empty Storage - Free Pool' (the zero-rate tier
    encodes Y, same convention as :func:`sql_storage_tariffs`'s free-days tier —
    occasionally it also carries the beyond-pool tiers itself, keyed by a TEU-
    count TierName rather than by day) and 'Empty Storage - Beyond Free Pool'
    (usually one flat non-tiered rate — TierStart/TierEnd are NULL in that
    common case; :meth:`data.repository.MovesSimRepository.get_empty_pool_tariff`
    treats a NULL tier as "0 to unbounded"). Both are merged into one tariff.
    """
    return (
        "SELECT rs.ActivityName AS activity_name, rs.TierStart AS tier_start, "
        "rs.TierEnd AS tier_end, rs.Rate AS rate, rs.Currency AS currency,\n"
        "       rs.RateSheetID AS RatesheetID, rs.RateSheetName, "
        "rs.EffectiveStartDate, rs.EffectiveEndDate\n"
        f"FROM {TABLE_CUSTOMER_RATE_SHEETS} rs\n"
        f"JOIN {TABLE_TERMINAL_MAP} t ON UPPER(TRIM(t.{term_raw})) = UPPER(TRIM(rs.Terminal))\n"
        f"JOIN {TABLE_CUSTOMER_MAP} cm ON UPPER(TRIM(cm.Operator)) = UPPER(TRIM(rs.Customer))\n"
        f"WHERE {_ci(f't.{term_std}', standard_terminal)}\n"
        f"  AND {_ci('cm.Standard_Operator_Code', standard_operator)}\n"
        "  AND UPPER(rs.CategoryName) = 'STORAGE SERVICES'\n"
        "  AND rs.ActivityName IN ('Empty Storage - Free Pool', 'Empty Storage - Beyond Free Pool')\n"
        "  AND rs.RateSheetStatus NOT IN ('REJECTED', 'DELETED', 'DRAFT')"
    )


def sql_empty_storage_tariff(standard_terminal, standard_operator,
                             term_raw="Raw_Terminal", term_std="Std_Terminal") -> str:
    """Empty Storage dwell-day tariff (Logic 2 — same shape as Full Storage, just
    ActivityName='Empty Storage' with no Import/Export/Transshipment split)."""
    return (
        "SELECT rs.ActivityName AS activity_name, rs.TierStart AS tier_start, "
        "rs.TierEnd AS tier_end, rs.Rate AS rate, rs.Currency AS currency,\n"
        "       rs.RateSheetID AS RatesheetID, rs.RateSheetName, "
        "rs.EffectiveStartDate, rs.EffectiveEndDate\n"
        f"FROM {TABLE_CUSTOMER_RATE_SHEETS} rs\n"
        f"JOIN {TABLE_TERMINAL_MAP} t ON UPPER(TRIM(t.{term_raw})) = UPPER(TRIM(rs.Terminal))\n"
        f"JOIN {TABLE_CUSTOMER_MAP} cm ON UPPER(TRIM(cm.Operator)) = UPPER(TRIM(rs.Customer))\n"
        f"WHERE {_ci(f't.{term_std}', standard_terminal)}\n"
        f"  AND {_ci('cm.Standard_Operator_Code', standard_operator)}\n"
        "  AND UPPER(rs.CategoryName) = 'STORAGE SERVICES'\n"
        "  AND rs.ActivityName = 'Empty Storage'\n"
        "  AND rs.RateSheetStatus NOT IN ('REJECTED', 'DELETED', 'DRAFT')"
    )


def sql_reefer_volume(terminal, operators, date_from, date_to) -> str:
    """Reefer container volume + total container-days for the period.

    ``UNIT_REQUIRES_POWER`` is the reefer flag (confirmed live: containers
    needing power at the terminal). ``container_days`` (Container_Count x
    DWELL_DAYS, not a naive AVG(DWELL_DAYS)) lets the caller compute a properly
    weighted average dwell — reefer's flat daily rate means no per-day
    histogram is needed, just the totals. Same raw terminal/operator convention
    as :func:`sql_storage_dwell`.
    """
    return (
        "SELECT SUM(s.Container_Count) AS container_count, "
        "SUM(s.Container_Count * s.DWELL_DAYS) AS container_days\n"
        f"FROM {TABLE_STORAGE_INSIGHTS} s\n"
        f"WHERE UPPER(s.TerminalName) = UPPER('{_q(terminal)}')\n"
        "  AND s.UNIT_REQUIRES_POWER = '1'\n"
        f"  AND s.Event_Start_Date >= '{_q(date_from)}'\n"
        f"  AND s.Event_Start_Date <= '{_q(date_to)}'\n"
        f"{_in_filter('s.CONTAINER_OPERATOR', operators)}"
    )


_REEFER_ACTIVITIES = (
    "'Daily Reefer Service', 'Daily Reefer Service - Electricity Only', "
    "'Daily Reefer Service - Monitoring Only', 'Reefer Plug-in or Unplug'"
)


def sql_reefer_tariff(standard_terminal, standard_operator,
                      term_raw="Raw_Terminal", term_std="Std_Terminal") -> str:
    """Reefer tariff rows for a standard terminal + operator: the bundled daily
    rate ('Daily Reefer Service') and the three unbundled components (one-time
    plug fee + separate daily electricity/monitoring rates).

    Standardized like :func:`sql_bem_quay_rates`; column aliases match what
    :func:`engine.pricing.choose_rate_sheet` expects.
    """
    return (
        "SELECT rs.ActivityName AS activity_name, rs.Rate AS rate, rs.Currency AS currency,\n"
        "       rs.RateSheetID AS RatesheetID, rs.RateSheetName, "
        "rs.EffectiveStartDate, rs.EffectiveEndDate\n"
        f"FROM {TABLE_CUSTOMER_RATE_SHEETS} rs\n"
        f"JOIN {TABLE_TERMINAL_MAP} t ON UPPER(TRIM(t.{term_raw})) = UPPER(TRIM(rs.Terminal))\n"
        f"JOIN {TABLE_CUSTOMER_MAP} cm ON UPPER(TRIM(cm.Operator)) = UPPER(TRIM(rs.Customer))\n"
        f"WHERE {_ci(f't.{term_std}', standard_terminal)}\n"
        f"  AND {_ci('cm.Standard_Operator_Code', standard_operator)}\n"
        f"  AND rs.ActivityName IN ({_REEFER_ACTIVITIES})\n"
        "  AND rs.RateSheetStatus NOT IN ('REJECTED', 'DELETED', 'DRAFT')"
    )


def sql_variable_cpm(standard_terminal, term_raw="Raw_Terminal", term_std="Std_Terminal") -> str:
    """Latest 'Variable CPM' from Cost_OS for a standard terminal (UPPER/TRIM join)."""
    return (
        'SELECT c."Value" AS variable_cpm, c.actual_date\n'
        f"FROM {TABLE_COST} c\n"
        f"JOIN {TABLE_TERMINAL_MAP} t ON UPPER(TRIM(t.{term_raw})) = UPPER(TRIM(c.Terminal_SalesForce))\n"
        f"WHERE {_ci(f't.{term_std}', standard_terminal)}\n"
        "  AND c.Metric = 'Variable CPM'\n"
        "ORDER BY c.actual_date DESC\n"
        "LIMIT 1"
    )


def sql_shiftings_occurrences(tos_terminal, operators, date_from, date_to) -> str:
    """Restow-on-board (shift) volume from GBL_Shift_on_board_simulator.

    Filtered on the raw selected terminal (volume sources use the picked TOS name,
    same as the moves query), by date and optional operator codes.
    """
    return (
        "SELECT s.UNIT_FREIGHT_GROUP, s.container_length, SUM(s.Moves) AS total_moves\n"
        f"FROM {TABLE_SHIFTINGS} s\n"
        f"WHERE {_ci('s.TERMINALNAME', tos_terminal)}\n"
        f"  AND s.event_date >= '{_q(date_from)}' AND s.event_date <= '{_q(date_to)}'\n"
        f"{_ci_in('s.CONTAINER_OPERATOR_ID', operators)}"
        "GROUP BY s.UNIT_FREIGHT_GROUP, s.container_length"
    )


def sql_terminals() -> str:
    return (
        "SELECT DISTINCT terminalname\n"
        f"FROM {TABLE_SERVICE_LIST}\n"
        "WHERE terminalname IS NOT NULL AND terminalname <> ''\n"
        "ORDER BY terminalname"
    )


def sql_operators(terminal=None) -> str:
    where = "WHERE unit_container_operator_id IS NOT NULL AND unit_container_operator_id <> ''\n"
    if terminal:
        where += f"  AND terminalname = '{_q(terminal)}'\n"
    return (
        "SELECT DISTINCT unit_container_operator_id\n"
        f"FROM {TABLE_SERVICE_LIST}\n"
        f"{where}"
        "ORDER BY unit_container_operator_id"
    )


def sql_services(terminal=None, operators=None) -> str:
    where = "WHERE service_name IS NOT NULL AND service_name <> ''\n"
    if terminal:
        where += f"  AND terminalname = '{_q(terminal)}'\n"
    where += _in_filter("unit_container_operator_id", operators)
    return (
        "SELECT DISTINCT service_name\n"
        f"FROM {TABLE_SERVICE_LIST}\n"
        f"{where}"
        "ORDER BY service_name"
    )
