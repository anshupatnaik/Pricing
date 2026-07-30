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
