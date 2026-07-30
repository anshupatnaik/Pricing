# Dremio connection helper (PAT) + analyses

Connect to the Maersk enterprise (self-hosted) Dremio at
`enterprisedremio.maersk-digital.net` using a Personal Access Token (PAT)
supplied via an environment variable, run SQL, and save results to CSV. The
token is never hardcoded or written to disk.

This folder holds both the **connection tool** and the **SQL/analyses** built on
top of it.

---

## Part 1 — The tool

### Files
- `dremio_client.py` — full client: test connectivity, run SQL (submit → poll →
  paginate results), print a preview, and optionally write a CSV.
- `connect_dremio.py` — minimal connectivity tester (single GET to an endpoint).
- `.env` / `.env.example` — holds `DREMIO_TOKEN` (gitignored).
- `requirements.txt` — just `requests`.

### How the client works (logic)
`DremioClient` wraps Dremio's REST job API. A query is four steps:

1. **Auth** — every request sends `Authorization: Bearer <PAT>`. The PAT is read
   from `$DREMIO_TOKEN` (shell env wins) or the `.env` file via a tiny built-in
   dotenv loader (`load_dotenv`, no external dep, strips BOM/quotes/`export`).
2. **Submit** — `POST /api/v3/sql {"sql": ...}` returns a `job id`.
3. **Poll** — `GET /api/v3/job/{id}` every 1.5 s until the job reaches a terminal
   state (`COMPLETED` / `CANCELED` / `FAILED`); non-completion raises
   `DremioError` with Dremio's message.
4. **Fetch** — `GET /api/v3/job/{id}/results` paginated at **500 rows/page**
   (Dremio's hard cap) until all `rowCount` rows are collected.

`client.query(sql)` runs all four and returns `(columns, rows)` where each row is
a dict keyed by column name. Catalog browsing uses
`GET /api/v3/catalog/by-path/<space>/<folder>/...` (see `test_connection` and the
exploration snippets below).

### Setup
```powershell
python -m pip install -r requirements.txt
```
Provide the token via `.env` (recommended) or a shell env var:
```ini
# .env
DREMIO_TOKEN=your-pat-here
# DREMIO_HOST=enterprisedremio.maersk-digital.net
```
```powershell
$env:DREMIO_TOKEN = '<your-PAT>'   # session-only alternative
```

> **Where do I log in?** There is no interactive login. You authenticate with a
> **Personal Access Token**, not a username/password, and not via the SSO page.
> Generate the PAT once in the Dremio web UI:
> 1. Open `https://enterprisedremio.maersk-digital.net` in a browser and sign in
>    with your normal Maersk SSO.
> 2. Top-right **user avatar → Account Settings → Personal Access Tokens**.
> 3. **Generate new token**, give it a name + expiry, copy it (shown once).
> 4. Paste it into `dremio_connect/.env` as `DREMIO_TOKEN=...`.
>
> After that the scripts log in automatically with that token — no browser
> needed. Rotate/regenerate the token from the same page when it expires.

> If `python` isn't found, Python 3.13 is installed at
> `%LOCALAPPDATA%\Programs\Python\Python313\python.exe`.

### Usage
```powershell
python dremio_client.py --test                              # verify connectivity
python dremio_client.py --sql-file haiphong_waiting.sql --csv out.csv
python dremio_client.py --sql-file sample_query.sql --max-rows 100
```

### IMPORTANT: quoting on PowerShell
PowerShell strips embedded double-quotes when passing args to native exes, so
Dremio identifiers like `"APMT-BEATS"` break via `--sql "..."`. **Prefer
`--sql-file`** (no shell quoting), or drive the client from a small Python
snippet (`import dremio_client`), as the analyses below do.

### Gotchas learned
- `year` and `month` are **reserved words** → quote them: `"year" = 2025`.
- `"month" / 3` is **integer division** in Dremio → mis-buckets quarters. Use an
  explicit `CASE WHEN "month" <= 3 THEN 'Q1' ...`.
- `/results` caps at 500 rows/page (handled by the client's pager).

---

## Part 2 — Analyses in this folder

Each analysis is a `.sql` file (run via `--sql-file`) with its `.csv` output.

| File | What it does |
|------|--------------|
| `sample_query.sql` | Alphaliner active-fleet smoke test (MINS space). |
| `top_terminals_moves.sql` | 2025 moves + revenue per terminal (MINS OneStream `OS_T`). |
| `gti_mumbai_2026.sql`, `gti_mumbai_yoy.sql` | GTI Mumbai volumes / YoY. |
| `portelizabeth_rates.sql` | Port Elizabeth rate pull. |
| **`haiphong_waiting.sql`** | **Vietnam river vs deep-water terminal waiting times (below).** |

### Vietnam waiting-time study — logic

**Question:** waiting times at Haiphong **river** terminals vs the **deep-water**
terminal, container ships, FY2025 with a Q1/Q2 2026-vs-2025 YoY check.

**Source:** `Container_Cloud.model.final.calls_with_move_count` — AIS-derived
vessel calls. Grain = **1 row per terminal call**. Relevant columns:
`Port`, `Terminal`, `vessel_type_ais`, `max_draft`, `length`, `vesteu`,
`Duration` (berth hours), `prev_leg_stationary_hours`, `"year"`, `"month"`.
> Sibling tables in the same folder: `calls_with_direction`,
> `vsl_in_terminal_with_call_interpolated`, `utilization*`. Discover any space
> with `GET /api/v3/catalog/by-path/<space>/<folder>`.

**Logic / decisions:**
1. **Filter** `Port = 'Haiphong'`, `vessel_type_ais = 'Container Ship'`.
2. **River vs deep-water split** — validated from the data, not assumed: only
   *Haiphong International Container Terminal* (HICT, Lach Huyen) shows deep-draft
   ships (avg draft **11.2 m**, LOA **285 m**, **~7,055 TEU**). Every other berth
   is ≤ 8.7 m draft / feeder-sized → **river**. Encoded as a `CASE` on `Terminal`.
3. **Waiting-time proxy** — there is no literal waiting field. Use
   `prev_leg_stationary_hours` (hours stationary/anchored on the approach leg
   before berthing). It is outlier-prone (laid-up vessels → thousands of hours),
   so headline metrics are the **MEDIAN** and a **mean capped at ≤ 120 h**; the
   single laid-up berth *Cang Transvina* is excluded. `Duration` (berth stay) is
   reported alongside for context.
4. **YoY** — same metrics grouped by an explicit quarter `CASE` for Q1/Q2 across
   2025 and 2026.

**Findings (FY2025):** river terminals wait ~50% longer (capped-mean ~10 h vs
~7 h; median 2 h vs 1 h) despite near-identical ~18 h berth stays — the
deep-water terminal turns 5× larger ships in the same time. **YoY:** waiting flat-
to-lower in both groups (no congestion build-up); deep-water calls up +30–40%
while river volumes are flat-to-down, i.e. cargo migrating downriver to Lach
Huyen without added delay.

---

## Next steps
- [ ] **Export** the FY2025 and YoY tables to CSV
      (`--sql-file haiphong_waiting.sql --csv haiphong_waiting_2025.csv`; uncomment
      block B for the quarterly file).
- [ ] **Per-terminal breakout** of the river group (currently pooled).
- [ ] **National view** — extend the same river-vs-deep-water logic to other
      Vietnam clusters: Cai Mep/Vung Tau (deep-water) vs Ho Chi Minh City
      (river), Da Nang, Qui Nhon.
- [ ] **Sharpen the waiting proxy** — `prev_leg_stationary_hours` covers the whole
      approach leg, not just anchorage off Haiphong. Investigate
      `vsl_in_terminal_with_call_interpolated` / `utilization*` for a
      geofenced anchorage-dwell signal, and cross-check against berth congestion.
- [ ] **Parameterise** `haiphong_waiting.sql` (port, vessel type, date range) into
      a reusable function in a small `analyses/` module.

## Security
Do NOT commit your PAT or any generated CSVs containing data. Rotate the token in
Dremio if it is ever shared or pasted in plain text.
