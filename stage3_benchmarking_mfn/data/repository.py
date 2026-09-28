"""Data-access layer: the only module that touches Dremio.

Wraps the existing ``dremio_connect.DremioClient`` and returns plain rows /
engine occurrence objects, so the engine never sees raw Dremio dicts and the UI
never builds SQL.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from engine.occurrences import (
    OOG_ITEM, OccurrenceRow, annualize, _days_between, gate_key, hazard_key, move_key,
)

from . import queries

# Make the sibling ``dremio_connect`` package importable regardless of CWD.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dremio_connect.dremio_client import DremioClient, DremioError, load_dotenv  # noqa: E402


def _f(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_tier_row(r) -> tuple[int, int, float] | None:
    """A Customer_Rate_Sheets tier row -> (start, end, rate), or None if unparseable.

    A non-tiered row (``tier_start``/``tier_end`` both NULL — the common flat-rate
    case, e.g. 'Empty Storage - Beyond Free Pool') becomes ``(0, UNBOUNDED)``:
    since :func:`engine.storage.revenue_per_container` always clips a tier's
    start to the tariff's ``free_days + 1`` anyway, a start of 0 is equivalent to
    "applies to everything past the free allowance" — exactly what a flat
    beyond-pool/beyond-free-days rate means.
    """
    from engine import storage
    if r.get("rate") in (None, ""):
        return None  # FREE_TEXT/description-only pricing — no structured rate to use
    try:
        start = int(float(r.get("tier_start"))) if r.get("tier_start") not in (None, "") else 0
        end = (int(float(r.get("tier_end"))) if r.get("tier_end") not in (None, "")
               else storage.UNBOUNDED_TIER_END)
        rate = float(r.get("rate"))
    except (TypeError, ValueError):
        return None
    return (start, end, rate)


def _storage_category_from_activity(activity_name) -> str | None:
    """'Full Storage - Import' -> 'IMPRT' (matches the dwell histogram's category
    codes); None for anything that isn't one of the three directions."""
    n = str(activity_name or "").lower()
    if "import" in n:
        return "IMPRT"
    if "export" in n:
        return "EXPRT"
    if "transshipment" in n or "transhipment" in n:
        return "TRSHP"
    return None


class MovesSimRepository:
    """Fetch vessel-moves inputs from Dremio for the SL revenue simulator."""

    def __init__(self, client: DremioClient) -> None:
        self.client = client
        self._term_cols = None  # cached (raw_col, std_col) for Terminal_mapping

    def terminal_cols(self) -> tuple[str, str]:
        """Detect the live Terminal_mapping column names (they flip upstream).

        Returns (raw_col, std_col), e.g. ('Raw_Terminal','Std_Terminal') or
        ('terminalName','Standard_Terminal'). Cached per repository.
        """
        if self._term_cols is None:
            cols, _ = self.client.query(f"SELECT * FROM {queries.TABLE_TERMINAL_MAP} LIMIT 1")
            raw = next((c for c in queries.TERM_RAW_CANDIDATES if c in cols), cols[0] if cols else "Raw_Terminal")
            std = next((c for c in queries.TERM_STD_CANDIDATES if c in cols),
                       (cols[1] if len(cols) > 1 else "Std_Terminal"))
            self._term_cols = (raw, std)
        return self._term_cols

    @classmethod
    def from_env(cls, token_env: str = "DREMIO_TOKEN") -> "MovesSimRepository":
        load_dotenv()
        token = os.environ.get(token_env)
        if not token:
            raise DremioError(
                f"env var {token_env} is not set. Copy dremio_connect/.env.example "
                f"to .env with your PAT, or set ${token_env} in the shell."
            )
        host = os.environ.get("DREMIO_HOST") or "enterprisedremio.maersk-digital.net"
        return cls(DremioClient(token, host=host))

    # -- pickers ----------------------------------------------------------
    def list_terminals(self) -> list[str]:
        _, rows = self.client.query(queries.sql_terminals())
        return [r["terminalname"] for r in rows if r.get("terminalname")]

    def list_operators(self, terminal=None) -> list[str]:
        _, rows = self.client.query(queries.sql_operators(terminal))
        return [r["unit_container_operator_id"] for r in rows if r.get("unit_container_operator_id")]

    def list_services(self, terminal=None, operators=None) -> list[str]:
        _, rows = self.client.query(queries.sql_services(terminal, operators))
        return [r["service_name"] for r in rows if r.get("service_name")]

    # -- occurrences ------------------------------------------------------
    def get_occurrences(
        self, terminal, operators, services, date_from, date_to,
        include_hazard=True, include_shiftings=True, include_gate=True,
        include_oog=True, include_overtime=True,
    ) -> list[OccurrenceRow]:
        """Aggregated occurrence rows: quay move-key + hazardous + restow-on-board
        + gate (Truck & Rail legs) + OOG + overtime day-hour buckets, annualized.

        Mirrors the vUSA PMS ``Automatic Ocurrences`` sheet. ``include_gate`` covers
        both Truck and Rail gate legs (workbook XOR rule)."""
        days = _days_between(date_from, date_to)
        _, moves = self.client.query(
            queries.sql_moves_occurrences(terminal, operators, services, date_from, date_to)
        )
        out: list[OccurrenceRow] = []
        for r in moves:
            fg, ev, ln = r.get("unit_freight_group"), r.get("event_type"), r.get("cont_length")
            if not fg or not ev or ln in (None, ""):
                continue
            cnt = _f(r.get("total_moves"))
            out.append(OccurrenceRow(item=move_key(fg, ev, ln), count=cnt,
                                     group="Vessel Moves-Gateway", vessel_move=True,
                                     annualized=annualize(cnt, days)))
        if include_hazard:
            _, haz = self.client.query(
                queries.sql_moves_hazard(terminal, operators, services, date_from, date_to)
            )
            for r in haz:
                imo, imdg = r.get("imo_indicator"), r.get("cargo_imdg_types")
                if not imo or not imdg:
                    continue
                cnt = _f(r.get("total_moves"))
                out.append(OccurrenceRow(item=hazard_key(imo, imdg), count=cnt,
                                         group="Surcharge - Hazardous Cargo", vessel_move=False,
                                         annualized=annualize(cnt, days)))
        if include_shiftings:
            _, shifts = self.client.query(
                queries.sql_shiftings_occurrences(terminal, operators, date_from, date_to)
            )
            for r in shifts:
                fg, ln = r.get("UNIT_FREIGHT_GROUP"), r.get("container_length")
                if not fg or ln in (None, ""):
                    continue
                cnt = _f(r.get("total_moves"))
                item = f"Restow on board-{fg}-{move_key('', '', ln).strip('-')}"
                out.append(OccurrenceRow(item=item, count=cnt,
                                         group="Vessel Moves-Restow on board", vessel_move=True,
                                         annualized=annualize(cnt, days)))
        if include_gate:
            # Truck & Rail gate legs (workbook XOR rule); vessel_move=False —
            # these are landside gate legs, not extra vessel moves.
            for mode, label, group in (("TRUCK", "Truck", "Truck Moves"),
                                       ("TRAIN", "Rail", "Rail Moves")):
                _, rows = self.client.query(
                    queries.sql_gate_leg_occurrences(
                        terminal, operators, services, date_from, date_to, mode)
                )
                for r in rows:
                    fg, ln = r.get("unit_freight_group"), r.get("cont_length")
                    if not fg or ln in (None, ""):
                        continue
                    cnt = _f(r.get("total_moves"))
                    out.append(OccurrenceRow(item=gate_key(label, fg, ln), count=cnt,
                                             group=group, vessel_move=False,
                                             annualized=annualize(cnt, days)))
        if include_oog:
            _, rows = self.client.query(
                queries.sql_oog_occurrences(terminal, operators, services, date_from, date_to)
            )
            cnt = _f(rows[0].get("total_moves")) if rows else 0.0
            if cnt:
                out.append(OccurrenceRow(item=OOG_ITEM, count=cnt, group="Surcharge - OOG",
                                         vessel_move=False, annualized=annualize(cnt, days)))
        if include_overtime:
            _, rows = self.client.query(
                queries.sql_overtime_occurrences(terminal, operators, services, date_from, date_to)
            )
            for r in rows:
                ind = r.get("overtime_indicator")
                if not ind:
                    continue
                cnt = _f(r.get("total_moves"))
                out.append(OccurrenceRow(item=str(ind), count=cnt,
                                         group="Overtime Vessel Moves", vessel_move=False,
                                         annualized=annualize(cnt, days)))
        return out

    # -- current rates from pricing (BEM) --------------------------------
    def standard_terminal(self, tos_terminal: str) -> str | None:
        """Resolve a TOS terminal to its Standard_Terminal (with overrides)."""
        from .crosswalk import TERMINAL_OVERRIDES
        if tos_terminal in TERMINAL_OVERRIDES:
            return TERMINAL_OVERRIDES[tos_terminal]
        raw, std = self.terminal_cols()
        _, rows = self.client.query(queries.sql_standard_terminal(tos_terminal, raw, std))
        return rows[0]["std_terminal"] if rows else None

    def get_variable_cpm(self, tos_terminal: str) -> float | None:
        """Latest Variable CPM (cost per move) for the terminal, from Cost_OS.

        Returned as a POSITIVE magnitude; the app applies it as a negative cost.
        """
        std = self.standard_terminal(tos_terminal)
        if not std:
            return None
        raw, std_col = self.terminal_cols()
        _, rows = self.client.query(queries.sql_variable_cpm(std, raw, std_col))
        return _f(rows[0].get("variable_cpm")) if rows else None

    def resolve_operator(self, operator: str) -> str:
        """Resolve a raw operator code/name to its Standard_Operator_Code (else itself)."""
        if not operator:
            return operator
        _, rows = self.client.query(queries.sql_standard_operator(operator))
        return rows[0]["sc"] if rows and rows[0].get("sc") else operator

    def list_pricing_operators(self, tos_terminal: str) -> list[dict]:
        """Standard operators (code+name) with quay rates at this terminal (picker)."""
        std = self.standard_terminal(tos_terminal)
        if not std:
            return []
        raw, std_col = self.terminal_cols()
        _, rows = self.client.query(queries.sql_pricing_operators(std, raw, std_col))
        return [{"code": r.get("sc"), "name": r.get("sn")} for r in rows if r.get("sc")]

    def get_current_rates(self, tos_terminal, operator, tos_keys, today,
                          basis_by_category=None, prefer_ratesheet_id=None,
                          is_standard_code=False) -> dict:
        """Current per-move rates for the given TOS keys, from the effective BEM sheet.

        ``operator`` is a raw operator code (resolved to its standard code) unless
        ``is_standard_code`` is True. Both terminal and customer are standardized via
        the Lookups. Returns ``{"rates": {...}, "sheet": <info>}``.
        """
        from engine import pricing
        from .crosswalk import QUAY_INCLUDE_ACTIVITIES
        std = self.standard_terminal(tos_terminal)
        std_op = operator if is_standard_code else self.resolve_operator(operator)
        if not std or not std_op:
            return {"rates": {}, "sheet": {"ratesheet_name": None, "ambiguous": False, "candidates": []}}
        raw, std_col = self.terminal_cols()
        _, rows = self.client.query(
            queries.sql_bem_quay_rates(std, std_op, QUAY_INCLUDE_ACTIVITIES, raw, std_col)
        )
        chosen, info = pricing.choose_rate_sheet(rows, today, prefer_id=prefer_ratesheet_id)
        rates = pricing.rates_for_keys(tos_keys, chosen, basis_by_category)
        return {"rates": rates, "sheet": info}

    def get_gate_rates(self, tos_terminal, operator, tos_keys, today,
                      prefer_ratesheet_id=None, is_standard_code=False) -> dict:
        """Current per-move Truck/Rail gate rates for the given TOS keys.

        Same terminal/operator standardization and effective-sheet pick as
        :meth:`get_current_rates`, scoped to BEM's ``Gate Operations`` category
        (``Gate Move Truck`` / ``Gate Move Rail``) — a separate rate source from
        quay ops, since gate legs aren't priced under ``Quay Operations``.
        """
        from engine import pricing
        from .crosswalk import GATE_INCLUDE_ACTIVITIES
        std = self.standard_terminal(tos_terminal)
        std_op = operator if is_standard_code else self.resolve_operator(operator)
        if not std or not std_op:
            return {"rates": {}, "sheet": {"ratesheet_name": None, "ambiguous": False, "candidates": []}}
        raw, std_col = self.terminal_cols()
        _, rows = self.client.query(
            queries.sql_bem_gate_rates(std, std_op, GATE_INCLUDE_ACTIVITIES, raw, std_col)
        )
        chosen, info = pricing.choose_rate_sheet(rows, today, prefer_id=prefer_ratesheet_id)
        rates = pricing.rates_for_keys(tos_keys, chosen)
        return {"rates": rates, "sheet": info}

    def get_oog_surcharge(self, tos_terminal, operator, base_ld_rate, today,
                          prefer_ratesheet_id=None, is_standard_code=False) -> dict:
        """Per-move OOG standard-spreader surcharge for the terminal + operator.

        Fetches surcharge BEM rows, picks the effective sheet, and resolves the OOG
        surcharge against ``base_ld_rate`` (the current Load/Discharge rate). Returns
        ``{"oog": <dict|None>, "sheet": <info>}``; ``oog`` is None when the terminal
        has no BEM OOG surcharge (falls back to manual entry, as with quay rates).
        """
        from engine import pricing
        empty = {"oog": None, "sheet": {"ratesheet_name": None, "ambiguous": False, "candidates": []}}
        std = self.standard_terminal(tos_terminal)
        std_op = operator if is_standard_code else self.resolve_operator(operator)
        if not std or not std_op:
            return empty
        raw, std_col = self.terminal_cols()
        _, rows = self.client.query(queries.sql_bem_surcharge_rates(std, std_op, raw, std_col))
        chosen, info = pricing.choose_rate_sheet(rows, today, prefer_id=prefer_ratesheet_id)
        return {"oog": pricing.oog_surcharge(chosen, base_ld_rate), "sheet": info}

    def get_overtime_rates(self, tos_terminal, operator, indicators, base_rate, today,
                           prefer_ratesheet_id=None, is_standard_code=False) -> dict:
        """Per-move overtime surcharge for each day-hour bucket ``indicator``.

        Fetches overtime BEM rows, picks the effective sheet, and matches each bucket
        by activity + day-band + time-band, resolving against ``base_rate``. Returns
        ``{"rates": {indicator: <dict>}, "sheet": <info>}`` (only matched buckets).
        """
        from engine import pricing
        empty = {"rates": {}, "sheet": {"ratesheet_name": None, "ambiguous": False, "candidates": []}}
        std = self.standard_terminal(tos_terminal)
        std_op = operator if is_standard_code else self.resolve_operator(operator)
        if not std or not std_op:
            return empty
        raw, std_col = self.terminal_cols()
        _, rows = self.client.query(queries.sql_bem_overtime_rates(std, std_op, raw, std_col))
        chosen, info = pricing.choose_rate_sheet(rows, today, prefer_id=prefer_ratesheet_id)
        out = {}
        for ind in indicators or []:
            r = pricing.overtime_rate(ind, chosen, base_rate)
            if r:
                out[ind] = r
        return {"rates": out, "sheet": info}

    def get_overtime_uplift(self, tos_terminal, operator, today,
                           prefer_ratesheet_id=None, is_standard_code=False) -> dict:
        """Blended overtime uplift % — the Detailed-mode alternative to per-bucket rates.

        Same effective-sheet pick as :meth:`get_overtime_rates`, but averages every
        eligible banded row into one % (:func:`engine.pricing.average_overtime_uplift`),
        matching the workbook's ``Overtime!D170``-style average that Simple mode
        already uses by default. Returns ``{'pct': <float>, 'sheet': <info>}``.
        """
        from engine import pricing
        empty = {"pct": 0.0, "sheet": {"ratesheet_name": None, "ambiguous": False, "candidates": []}}
        std = self.standard_terminal(tos_terminal)
        std_op = operator if is_standard_code else self.resolve_operator(operator)
        if not std or not std_op:
            return empty
        raw, std_col = self.terminal_cols()
        _, rows = self.client.query(queries.sql_bem_overtime_rates(std, std_op, raw, std_col))
        chosen, info = pricing.choose_rate_sheet(rows, today, prefer_id=prefer_ratesheet_id)
        return {"pct": pricing.average_overtime_uplift(chosen), "sheet": info}

    # -- Full Storage (dwell x tariff) -------------------------------------
    def get_storage_dwell(self, terminal, operators, date_from, date_to) -> list:
        """Full-container dwell buckets (:class:`engine.storage.DwellBucket`) for
        the raw selected terminal + operator codes (same volume-source convention
        as :meth:`get_occurrences` — no Std_Terminal join needed)."""
        from engine.storage import DwellBucket

        _, rows = self.client.query(queries.sql_storage_dwell(terminal, operators, date_from, date_to))
        return [
            DwellBucket(category=str(r.get("category") or ""),
                       dwell_days=int(_f(r.get("dwell_days"))),
                       container_count=_f(r.get("container_count")))
            for r in rows
        ]

    def get_storage_tariffs(self, tos_terminal, operator, today,
                            prefer_ratesheet_id=None, is_standard_code=False) -> dict:
        """Full Storage tariff per category (IMPRT/EXPRT/TRSHP) for a terminal +
        operator, from the effective-today Customer_Rate_Sheets sheet.

        Same terminal/operator standardization and effective-sheet pick as
        :meth:`get_current_rates`. Returns ``{'tariffs': {category:
        engine.storage.StorageTariff}, 'sheet': <info>}``.
        """
        from engine import pricing, storage
        empty = {"tariffs": {}, "sheet": {"ratesheet_name": None, "ambiguous": False, "candidates": []}}
        std = self.standard_terminal(tos_terminal)
        std_op = operator if is_standard_code else self.resolve_operator(operator)
        if not std or not std_op:
            return empty
        raw, std_col = self.terminal_cols()
        _, rows = self.client.query(queries.sql_storage_tariffs(std, std_op, raw, std_col))
        chosen, info = pricing.choose_rate_sheet(rows, today, prefer_id=prefer_ratesheet_id)
        by_category: dict[str, list] = {}
        for r in chosen:
            cat = _storage_category_from_activity(r.get("activity_name"))
            tier = _parse_tier_row(r)
            if cat is None or tier is None:
                continue
            by_category.setdefault(cat, []).append(tier)
        tariffs = {cat: storage.build_tariff(tiers) for cat, tiers in by_category.items()}
        return {"tariffs": tariffs, "sheet": info}

    # -- Empty Storage: Logic 2 (same dwell-day model as Full Storage) ----
    EMPTY_CATEGORY = "EMPTY"

    def get_empty_storage_dwell(self, terminal, operators, date_from, date_to) -> list:
        """Empty-container dwell buckets, tagged :data:`EMPTY_CATEGORY` so they
        plug directly into :func:`engine.storage.total_storage_revenue` like
        Full Storage's per-category buckets."""
        from engine.storage import DwellBucket

        _, rows = self.client.query(
            queries.sql_empty_storage_dwell(terminal, operators, date_from, date_to))
        return [
            DwellBucket(category=self.EMPTY_CATEGORY, dwell_days=int(_f(r.get("dwell_days"))),
                       container_count=_f(r.get("container_count")))
            for r in rows
        ]

    def get_empty_storage_tariff(self, tos_terminal, operator, today,
                                 prefer_ratesheet_id=None, is_standard_code=False) -> dict:
        """Empty Storage dwell-day tariff ('Empty Storage' activity — free days,
        then day-tiers, same shape as Full Storage). Returns ``{'tariff':
        engine.storage.StorageTariff, 'sheet': <info>}``."""
        from engine import pricing, storage
        empty = {"tariff": None, "sheet": {"ratesheet_name": None, "ambiguous": False, "candidates": []}}
        std = self.standard_terminal(tos_terminal)
        std_op = operator if is_standard_code else self.resolve_operator(operator)
        if not std or not std_op:
            return empty
        raw, std_col = self.terminal_cols()
        _, rows = self.client.query(queries.sql_empty_storage_tariff(std, std_op, raw, std_col))
        chosen, info = pricing.choose_rate_sheet(rows, today, prefer_id=prefer_ratesheet_id)
        tiers = [t for t in (_parse_tier_row(r) for r in chosen) if t is not None]
        return {"tariff": storage.build_tariff(tiers), "sheet": info}

    # -- Empty Storage: Logic 1 (daily free-pool allowance) ----------------
    def get_empty_pool_tariff(self, tos_terminal, operator, today,
                              prefer_ratesheet_id=None, is_standard_code=False) -> dict:
        """Empty Storage free-pool tariff (pool size Y as the zero-rate tier +
        the beyond-pool rate/tiers, merged from 'Empty Storage - Free Pool' and
        'Empty Storage - Beyond Free Pool'). A non-tiered beyond-pool row (no
        TierStart/TierEnd — the common case) is treated as "0 to unbounded".
        Returns ``{'tariff': engine.storage.StorageTariff, 'sheet': <info>}``.
        """
        from engine import pricing, storage
        empty = {"tariff": None, "sheet": {"ratesheet_name": None, "ambiguous": False, "candidates": []}}
        std = self.standard_terminal(tos_terminal)
        std_op = operator if is_standard_code else self.resolve_operator(operator)
        if not std or not std_op:
            return empty
        raw, std_col = self.terminal_cols()
        _, rows = self.client.query(queries.sql_empty_pool_tariff(std, std_op, raw, std_col))
        chosen, info = pricing.choose_rate_sheet(rows, today, prefer_id=prefer_ratesheet_id)
        tiers = [t for t in (_parse_tier_row(r) for r in chosen) if t is not None]
        return {"tariff": storage.build_tariff(tiers), "sheet": info}

    def get_empty_daily_occupancy(self, terminal, operators, date_from, date_to) -> dict:
        """Empty-container TEU occupancy per calendar day over the period.

        Expands each presence interval (start date, end date, TEU/container x
        container_count) across every day it covers, clipped to [date_from,
        date_to], and sums TEU per day — dwell time itself never enters the
        calculation, only how many TEU are present on a given day. Returns
        ``{iso_date: total_teu}`` for every day the terminal had any presence
        (a day with none simply doesn't appear — treat as 0).
        """
        from datetime import date as _date, timedelta

        def _parse_date(s):
            y, m, d = str(s)[:10].split("-")
            return _date(int(y), int(m), int(d))

        lo, hi = _parse_date(date_from), _parse_date(date_to)
        _, rows = self.client.query(
            queries.sql_empty_dwell_daily(terminal, operators, date_from, date_to)
        )
        occupancy: dict[str, float] = {}
        for r in rows:
            try:
                start = max(_parse_date(r.get("start_date")), lo)
                end = min(_parse_date(r.get("end_date")), hi)
            except (TypeError, ValueError):
                continue
            if start > end:
                continue
            teu = _f(r.get("teu_per_container")) * _f(r.get("container_count"))
            day = start
            while day <= end:
                key = day.isoformat()
                occupancy[key] = occupancy.get(key, 0.0) + teu
                day += timedelta(days=1)
        return occupancy

    # -- Reefer storage (flat daily rate x avg dwell; no tiering) ----------
    def get_reefer_volume(self, terminal, operators, date_from, date_to) -> dict:
        """Reefer container count + weighted average dwell days for the period.

        Returns ``{'container_count': float, 'avg_dwell_days': float}``. The
        average is container_days / container_count (weighted by each row's
        Container_Count), not a naive per-row mean.
        """
        _, rows = self.client.query(
            queries.sql_reefer_volume(terminal, operators, date_from, date_to))
        count = _f(rows[0].get("container_count")) if rows else 0.0
        days = _f(rows[0].get("container_days")) if rows else 0.0
        return {"container_count": count, "avg_dwell_days": (days / count) if count else 0.0}

    def get_reefer_tariff(self, tos_terminal, operator, today,
                          prefer_ratesheet_id=None, is_standard_code=False) -> dict:
        """Reefer rates for a terminal + operator: the bundled daily rate and
        the three unbundled components. Returns ``{'bundled_daily_rate',
        'plug_fee', 'electricity_daily', 'monitoring_daily'}`` (each ``None``
        when that activity has no signed rate) plus ``'sheet'``.
        """
        from engine import pricing
        empty = {"bundled_daily_rate": None, "plug_fee": None, "electricity_daily": None,
                 "monitoring_daily": None, "sheet": {"ratesheet_name": None, "ambiguous": False, "candidates": []}}
        std = self.standard_terminal(tos_terminal)
        std_op = operator if is_standard_code else self.resolve_operator(operator)
        if not std or not std_op:
            return empty
        raw, std_col = self.terminal_cols()
        _, rows = self.client.query(queries.sql_reefer_tariff(std, std_op, raw, std_col))
        chosen, info = pricing.choose_rate_sheet(rows, today, prefer_id=prefer_ratesheet_id)
        by_activity: dict[str, float] = {}
        for r in chosen:
            name = r.get("activity_name")
            if name not in by_activity and r.get("rate") not in (None, ""):
                try:
                    by_activity[name] = float(r.get("rate"))
                except (TypeError, ValueError):
                    continue
        return {
            "bundled_daily_rate": by_activity.get("Daily Reefer Service"),
            "plug_fee": by_activity.get("Reefer Plug-in or Unplug"),
            "electricity_daily": by_activity.get("Daily Reefer Service - Electricity Only"),
            "monitoring_daily": by_activity.get("Daily Reefer Service - Monitoring Only"),
            "sheet": info,
        }

    def get_shares(self, terminal, operators, services, date_from, date_to,
                   reefer_dwell: float = 1.0) -> dict:
        """Compute simple-mode move-type shares from Dremio (see engine.shares)."""
        from engine.shares import compute_shares

        _, cat_rows = self.client.query(
            queries.sql_category_breakdown(terminal, operators, services, date_from, date_to)
        )

        def _indicator(kind):
            _, rows = self.client.query(
                queries.sql_indicator_total(terminal, operators, services, date_from, date_to, kind)
            )
            return _f(rows[0].get("total_moves")) if rows else 0.0

        return compute_shares(
            cat_rows,
            reefer_moves=_indicator("reefer"),
            oog_moves=_indicator("oog"),
            imo_moves=_indicator("imo"),
            reefer_dwell=reefer_dwell,
        )
