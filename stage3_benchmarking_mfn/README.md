# Stage 3 `benchmark_mfn` — Shipping-Line Revenue Simulation Tool

A Streamlit tool that rebuilds two Excel pricing simulators in Python, driven live from Dremio,
so a pricing manager can test the revenue impact of different rate scenarios and get a
**per-scenario revenue-simulation summary**.

Two modes over one pure engine:

- **Detailed (PMS)** — rebuild of `Pricing Module Simulator Production version.xlsm`. Pulls vessel
  moves from Dremio, derives billable **occurrences** (`Full-Load-40` etc.), multiplies by
  manager-entered **rates per scenario** ÷ RoE, and rolls up **SL + BCO revenue, variable cost,
  contribution margin, and RPM**.
- **Simple (Hapag)** — rebuild of the `Hapag simulations Vado 2026-2027.xlsx` **"Vado HMM (2)"**
  tab. One annual volume × move-type **shares** × rates, with **overtime** uplift, rebate,
  surcharges, storage and empty-pool lines. Scenarios use **named roles** (Current/Floor/Target/
  Competitor/…).

### Simple-mode workflow (matches the pricing manager's process)
- **Shares auto-computed from Dremio** — "Prefill volume + shares" sets the volume mix
  (gateway full/empty, transhipment, shift, reefer, oog, imo) as each category's moves ÷ total
  (storage excluded). Reproduces the manager's pivot exactly. All shares overridable.
- **Current rates via rate-sheet upload** — upload a CSV/XLSX; the tool fuzzy-matches line items
  and fills the Current column (or type them). 
- **Other scenarios derive by %** — the scenarios table has a role, a **% applied to Current**
  (`rate = current × (1 + %)`) and a **comment**; Floor/Target/Anchor/Competition/CPI are derived,
  and **any rate is overridable** in the override grid.

### Current rates from the pricing system (both modes)
"Pull current rates from Pricing (Dremio)" auto-fills the **Current** column from the RM
benchmarking data (`Pricing Automation Workflow.Benchmarking.BEM_Pricing_Base`):
- Terminal is standardized via `Lookups.Terminal_mapping` (with a `Vado2` override); the BEM
  **pricing customer** is auto-suggested from the operator and pickable.
- Only **effective-today** quay load/discharge rates are used; if HQ and local sheets tie on dates,
  you're asked to pick one (or upload). Rates are **per single move** (matching TOS volume); a
  per-cycle toggle halves the rate for transshipment/restow when needed.
- TOS move keys (`Full-Discharge-20`) map to BEM SKUs; only 20/40/45 ft; storage excluded.
- Terminals with no BEM rates fall back to rate-sheet upload / manual entry.
See the `pricing-rate-pull` skill and `reference/crosswalk_draft.json` for the full logic.

### Deal Tracker
A second page records each simulation as a **closed deal** (pick the scenario the customer closed
on). It then shows how many deals closed **at / above / below CPI**, the **revenue upside vs
current**, and a per-deal table. Stored locally in `deal_records.json` (gitignored).

## Layout

```
engine/          pure model (no I/O): models, occurrences, revenue, result, simple_model, overtime, methodology
data/            Dremio access only: queries.py (SQL), repository.py (MovesSimRepository)
app/             streamlit_app.py (two modes) + summary.py
tests/           unit + parity tests (fixtures/ hold workbook-extracted parity data)
reference/       extracted Power Query M, VBA, and reverse-engineering notes (source of truth)
storage_legacy/  the earlier storage-tariff simulator, parked (superseded)
```

## Setup

```powershell
python -m pip install -r stage3_benchmarking_mfn/requirements.txt
```

### Dremio token — set it ONCE (no re-typing, no per-session env var)

Store your Personal Access Token in **one place**: `dremio_connect/.env` (this file is gitignored,
so the token is never committed). It should contain a single line:

```ini
DREMIO_TOKEN=your-token-here
```

The app reads this automatically. **Do NOT run `$env:DREMIO_TOKEN = ...`** — a shell/environment
variable overrides `.env`, and a stale or placeholder value there is the usual cause of `HTTP 401`.
When the token eventually expires, generate a new one in Dremio (pick the longest allowed expiry)
and update **only** that one line in `.env`.

> The app validates the token at startup: the sidebar shows "Connected to Dremio" only if it truly
> works, otherwise it reports the error and falls back to manual data entry.

## Run

**Easiest:** double-click **`stage3_benchmarking_mfn\run_simulator.bat`** (opens the app at
http://localhost:8600).

Or from a terminal (no token line needed — `.env` is used automatically):

```powershell
python -m streamlit run "stage3_benchmarking_mfn\app\streamlit_app.py" --server.port 8600
```

Pick a mode, set terminal / operators / services / dates, configure scenarios (name + role),
enter rates and assumptions, and read the **Revenue simulation summary** (table + charts + CSV).

## Tests

```powershell
cd stage3_benchmarking_mfn
python -m pytest -q
```

- **Hapag parity** (`test_simple_parity.py`) reproduces the workbook's "Vado HMM (2)" outputs
  **exactly** (Total Quay, Total, Total-after-rebate, RPM for Maersk/Hapag/HMM-Floor).
- **Engine unit tests** (`test_engine.py`) cover occurrence derivation, `occ×rate/RoE`, deltas,
  overtime averaging, CPI/ordering, and edge cases.
- **PMS parity** (`test_pms_parity.py`) matches the workbook's `SL Revenue per Ocurrence` row-39
  totals. The shipped PMS file is a clean template (occurrences all 0), so **live numeric parity
  needs real data** — validate via a DAL smoke test:

  ```powershell
  python dremio_connect/dremio_client.py --sql-file stage3_benchmarking_mfn/data/sql/moves_occurrences.sql --max-rows 50
  ```

## Methodology & assumptions

Every assumption / manager decision / input surface is documented as a Claude Code skill under
`.claude/skills/` (scenario roles, occurrence normalization, overtime, variable cost & margin,
BCO revenue, rebate/empty-pool/storage, Dremio sources). All pricing-role logic lives in
`engine/methodology.py`.

### Known caveats
- The PMS `Variable Cost` sheet has `#REF!` errors; we implement the intended
  `variable_cost_per_move × moves` logic from the `Result` sheet and do not replicate the broken
  cells.
- Source `.xlsm`/`.xlsx` files are gitignored (may contain sensitive rate/volume data).
