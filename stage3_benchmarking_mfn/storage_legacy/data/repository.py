"""Data-access layer: the only module that touches Dremio.

Wraps the existing ``dremio_connect.DremioClient`` and maps result rows into the
engine's :class:`RawRow` dataclass, so the engine never sees raw Dremio dicts
and the UI never builds SQL.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from engine.models import RawRow

from . import queries

# Make the sibling ``dremio_connect`` package importable regardless of CWD.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dremio_connect.dremio_client import DremioClient, DremioError, load_dotenv  # noqa: E402


def _to_float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value) -> int | None:
    f = _to_float(value)
    return None if f is None else int(f)


class StorageSimRepository:
    """Fetch storage-simulator inputs from Dremio and return engine models."""

    FREIGHT_KIND = "Full"  # every query filters freight_kind = 'Full'

    def __init__(self, client: DremioClient) -> None:
        self.client = client

    @classmethod
    def from_env(cls, token_env: str = "DREMIO_TOKEN") -> "StorageSimRepository":
        """Build a repository using the same PAT/.env convention as the CLI."""
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

    def list_operators(self, terminal: str | None = None) -> list[str]:
        _, rows = self.client.query(queries.sql_operators(terminal))
        return [r["container_operator"] for r in rows if r.get("container_operator")]

    # -- data -------------------------------------------------------------
    def get_rows(
        self,
        cargo_type: str,
        terminal: str,
        operators,
        date_from: str,
        date_to: str,
    ) -> list[RawRow]:
        """Aggregated occurrence rows for one cargo stream as :class:`RawRow`."""
        sql = queries.sql_raw(cargo_type, terminal, operators, date_from, date_to)
        _, rows = self.client.query(sql)
        out: list[RawRow] = []
        for r in rows:
            dwell = _to_int(r.get("dwell_days"))
            count = _to_float(r.get("container_count"))
            length = _to_float(r.get("container_length"))
            category = r.get("unit_category_fixed")
            if dwell is None or count is None or length is None or not category:
                continue
            out.append(
                RawRow(
                    category=category,
                    freight_kind=self.FREIGHT_KIND,
                    dwell_days=dwell,
                    container_count=count,
                    container_length=length,
                    terminal=terminal,
                    cargo_type=cargo_type,
                )
            )
        return out
