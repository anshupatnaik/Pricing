#!/usr/bin/env python3
"""Dremio client for the Maersk enterprise (self-hosted) Dremio.

Connects with a Personal Access Token (PAT) read from an environment variable
and runs SQL via the REST job API (submit -> poll -> fetch results, with
pagination). The token is NEVER hardcoded or written to disk by this module.

Quick start (PowerShell):
    $env:DREMIO_TOKEN = '<your-PAT>'
    python dremio_client.py --sql 'SELECT 1'

Run a query against the Alphaliner active fleet and save to CSV:
    python dremio_client.py `
      --sql 'SELECT * FROM "APMT-BEATS"."Global"."insights_and_visualizations"."MINS"."Alphaliner"."mins_active_fleet"' `
      --csv mins_active_fleet.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterator

import requests

DEFAULT_HOST = "enterprisedremio.maersk-digital.net"
DEFAULT_TOKEN_ENV = "DREMIO_TOKEN"
# Dremio caps a single /results call at 500 rows; we page through in chunks.
RESULTS_PAGE_SIZE = 500
TERMINAL_STATES = {"COMPLETED", "CANCELED", "FAILED"}


class DremioError(RuntimeError):
    """Raised when Dremio returns an error or a job does not complete."""


class DremioClient:
    def __init__(
        self,
        token: str,
        host: str = DEFAULT_HOST,
        scheme: str = "https",
        verify: bool = True,
        timeout: int = 30,
    ) -> None:
        if not token:
            raise DremioError("No PAT provided. Set the token env var first.")
        self.base = f"{scheme}://{host}"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = verify
        self.session.headers.update(
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )

    # -- low-level helpers -------------------------------------------------
    def _get(self, path: str, **params: Any) -> dict:
        r = self.session.get(f"{self.base}{path}", params=params, timeout=self.timeout)
        self._raise_for_status(r)
        return r.json()

    def _post(self, path: str, payload: dict) -> dict:
        r = self.session.post(f"{self.base}{path}", json=payload, timeout=self.timeout)
        self._raise_for_status(r)
        return r.json()

    @staticmethod
    def _raise_for_status(resp: requests.Response) -> None:
        if resp.status_code >= 400:
            raise DremioError(f"HTTP {resp.status_code} for {resp.url}: {resp.text[:500]}")

    # -- public API --------------------------------------------------------
    def test_connection(self) -> list[str]:
        """Return the top-level catalog container names (proves auth works)."""
        data = self._get("/api/v3/catalog").get("data", [])
        return [".".join(item.get("path", [])) for item in data]

    def submit_sql(self, sql: str) -> str:
        """Submit a SQL statement and return the job id."""
        return self._post("/api/v3/sql", {"sql": sql})["id"]

    def wait_for_job(self, job_id: str, poll_secs: float = 1.5, max_wait: int = 600) -> dict:
        """Poll a job until it reaches a terminal state."""
        deadline = time.time() + max_wait
        last = {}
        while time.time() < deadline:
            last = self._get(f"/api/v3/job/{job_id}")
            state = last.get("jobState")
            if state in TERMINAL_STATES:
                if state != "COMPLETED":
                    msg = last.get("errorMessage", "(no error message)")
                    raise DremioError(f"Job {job_id} ended in {state}: {msg}")
                return last
            time.sleep(poll_secs)
        raise DremioError(f"Job {job_id} did not finish within {max_wait}s")

    def fetch_results(self, job_id: str, max_rows: int | None = None) -> tuple[list[str], list[dict]]:
        """Fetch all (or up to max_rows) result rows, paging as needed.

        Returns (column_names, rows) where each row is a dict keyed by column.
        """
        first = self._get(f"/api/v3/job/{job_id}/results", offset=0, limit=RESULTS_PAGE_SIZE)
        total = first.get("rowCount", 0)
        columns = [c["name"] for c in first.get("schema", [])]
        rows: list[dict] = list(first.get("rows", []))

        target = total if max_rows is None else min(total, max_rows)
        while len(rows) < target:
            page = self._get(
                f"/api/v3/job/{job_id}/results", offset=len(rows), limit=RESULTS_PAGE_SIZE
            )
            batch = page.get("rows", [])
            if not batch:
                break
            rows.extend(batch)
        return columns, rows[:target] if max_rows is not None else rows

    def query(self, sql: str, max_rows: int | None = None) -> tuple[list[str], list[dict]]:
        """Convenience: submit -> wait -> fetch. Returns (columns, rows)."""
        job_id = self.submit_sql(sql)
        self.wait_for_job(job_id)
        return self.fetch_results(job_id, max_rows=max_rows)


def load_dotenv(path: str | os.PathLike | None = None, override: bool = False) -> dict[str, str]:
    """Minimal .env loader (no external dependency).

    Reads KEY=VALUE lines from a .env file and sets them in os.environ. Existing
    environment variables win unless override=True. Supports # comments, blank
    lines, optional surrounding single/double quotes, and a leading 'export '.

    Search order when path is None: ./ .env, then the .env next to this script.
    Returns the dict of keys that were applied.
    """
    if path is None:
        candidates = [Path.cwd() / ".env", Path(__file__).resolve().parent / ".env"]
    else:
        candidates = [Path(path)]

    applied: dict[str, str] = {}
    env_file = next((p for p in candidates if p.is_file()), None)
    if env_file is None:
        return applied

    # utf-8-sig strips a BOM if present (Windows editors / PowerShell often add one).
    for raw in env_file.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.lower().startswith("export "):
            line = line[len("export "):]
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = value
            applied[key] = value
    return applied


def _load_token(token_env: str) -> str:
    load_dotenv()
    token = os.environ.get(token_env)
    if not token:
        sys.exit(
            f"Error: env var {token_env} is not set.\n"
            f"  Option A (.env file):  copy .env.example to .env and paste your PAT\n"
            f"  Option B (PowerShell): $env:{token_env} = '<your-PAT>'"
        )
    return token


def _write_csv(path: str, columns: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _print_preview(columns: list[str], rows: list[dict], n: int = 10) -> None:
    print(f"columns ({len(columns)}): {', '.join(columns)}")
    print(f"rows returned: {len(rows)}")
    print(f"--- first {min(n, len(rows))} rows ---")
    for row in rows[:n]:
        print({k: row.get(k) for k in columns})


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Query the Maersk enterprise Dremio with a PAT.")
    p.add_argument("--host", default=None,
                   help=f"Dremio host (default: $DREMIO_HOST or {DEFAULT_HOST})")
    p.add_argument("--token-env", default=DEFAULT_TOKEN_ENV,
                   help=f"Env var holding the PAT (default: {DEFAULT_TOKEN_ENV})")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--test", action="store_true", help="Just verify connectivity (list catalog)")
    g.add_argument("--sql", help="SQL statement to run")
    g.add_argument("--sql-file", help="Path to a file containing the SQL statement")
    p.add_argument("--csv", help="Write results to this CSV path")
    p.add_argument("--max-rows", type=int, default=None, help="Cap the number of rows fetched")
    p.add_argument("--no-verify", action="store_true", help="Disable TLS verification (not recommended)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    token = _load_token(args.token_env)  # also loads .env
    host = args.host or os.environ.get("DREMIO_HOST") or DEFAULT_HOST
    client = DremioClient(token, host=host, verify=not args.no_verify)

    try:
        if args.test:
            names = client.test_connection()
            print(f"Connected to {host}. Top-level catalog containers ({len(names)}):")
            for n in names:
                print(f"  - {n}")
            return 0

        sql = args.sql
        if args.sql_file:
            with open(args.sql_file, "r", encoding="utf-8") as f:
                sql = f.read()

        columns, rows = client.query(sql, max_rows=args.max_rows)
        _print_preview(columns, rows)
        if args.csv:
            _write_csv(args.csv, columns, rows)
            print(f"Wrote {len(rows)} rows to {args.csv}")
        return 0
    except DremioError as e:
        print(f"Dremio error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
