"""Streamlit UI for the Shipping-Line Revenue Simulation tool.

Pages:
  * Simulate    - Detailed (PMS) or Simple (Hapag) revenue simulation across scenarios.
  * Deal Tracker - review closed deals: at/above/below CPI and revenue upside.

Run:  streamlit run stage3_benchmarking_mfn/app/streamlit_app.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

_STAGE3 = Path(__file__).resolve().parents[1]
if str(_STAGE3) not in sys.path:
    sys.path.insert(0, str(_STAGE3))

from engine.models import MODE_DETAILED, MODE_SIMPLE, ROLES, Scenario, finalize_summary  # noqa: E402
from engine.methodology import derive_from_pct, validate_ordering  # noqa: E402
from engine.occurrences import OOG_ITEM  # noqa: E402
from engine.pricing import parse_overtime_indicator  # noqa: E402
from engine.result import run_detailed  # noqa: E402
from engine.revenue import PmsItem, sl_revenue_per_item  # noqa: E402
from engine.simple_model import SimpleInputs, run_simple  # noqa: E402
from engine import deals as deals_mod  # noqa: E402
from app.summary import components_frame, summary_to_frame  # noqa: E402
from app.ratesheet import parse_rate_sheet, parse_rate_sheet_by_item  # noqa: E402
from app import store  # noqa: E402
from datetime import date  # noqa: E402

TODAY = date.today().isoformat()
# Representative Load/Discharge keys that OOG/overtime surcharges are priced "on top of".
_LD_BASE_KEYS = ("Full-Discharge-40", "Full-Load-40", "Full-Discharge-20", "Full-Load-20")


def _representative_ld_rate(px_rates: dict) -> float:
    """A representative current Load/Discharge rate that percentage surcharges
    (OOG, overtime) apply on top of. Prefers Full L/D 40ft, else any gateway L/D."""
    for k in _LD_BASE_KEYS:
        if px_rates.get(k):
            return float(px_rates[k])
    ld = [float(v) for k, v in px_rates.items() if v and ("-Load-" in k or "-Discharge-" in k)]
    return max(ld) if ld else 0.0


# Simple-mode line -> representative TOS key (to pull a per-move pricing rate)
SIMPLE_LINE_KEYS = {
    "full_ld": "Full-Load-40", "empty_ld": "Empty-Load-40",
    "transhipment": "Transhipment-Full-40", "shift": "Restow via quay-Full-40",
    "gate_full": "Full-Discharge-40", "gate_empty": "Empty-Discharge-40",
}


def pricing_operator_ui(repo, terminal, operators, keyprefix):
    """Selectbox of standard operators with quay rates at the terminal.

    Auto-suggests from the sidebar-selected operator (resolved to its standard
    code). Returns the chosen Standard_Operator_Code.
    """
    if repo is None or not terminal:
        return None
    try:
        ops = repo.list_pricing_operators(terminal)
    except Exception as e:  # noqa: BLE001
        st.caption(f"(pricing operators unavailable: {e})")
        return None
    if not ops:
        st.caption("No pricing operators found for this terminal (rates via upload/manual).")
        return None
    codes = [o["code"] for o in ops]
    labels = {o["code"]: f"{o['name']} ({o['code']})" for o in ops}
    suggested = None
    for op in (operators or []):
        std = repo.resolve_operator(op)
        if std in codes:
            suggested = std
            break
    idx = codes.index(suggested) if suggested in codes else 0
    return st.selectbox("Pricing operator", codes, index=idx,
                        format_func=lambda c: labels.get(c, c), key=keyprefix + "_op")


def show_sheet_info(sheet):
    if not sheet:
        return
    if sheet.get("ratesheet_name"):
        st.caption(f"📄 Rate sheet: {sheet['ratesheet_name']}")
    if sheet.get("ambiguous"):
        st.warning("Multiple effective rate sheets share the same start & end dates — "
                   "pick the correct one, or upload a rate sheet instead.")
        for c in sheet.get("candidates", []):
            st.caption(f"   • {c['name']}  ({c['start']} → {c['end']})")

st.set_page_config(page_title="SL Revenue Simulator", layout="wide")

SIMPLE_LINES = ["full_ld", "empty_ld", "transhipment", "shift",
                "gate_full", "gate_empty", "reefer"]
SHARE_KEYS = ["full_ld", "empty_ld", "transhipment", "shift",
              "gate_full", "gate_empty", "reefer", "reefer_dwell", "oog", "imo"]
DEFAULT_SCENARIOS = [
    ("Current", "current", 0.0, "Rates charged today (baseline)"),
    ("Floor", "floor", -0.05, "Walk-away minimum"),
    ("Target", "target", 0.10, "Aspirational"),
    ("Anchor", "anchor", 0.03, "Opening ask"),
    ("Competition", "competitor", 0.0, "Benchmark line / MFN"),
    ("CPI", "cpi", 0.017, "Current escalated by CPI"),
]


@st.cache_resource(show_spinner=False)
def get_repo():
    """Build the repo AND validate the token, so the sidebar status is truthful."""
    try:
        from data.repository import MovesSimRepository
        repo = MovesSimRepository.from_env()
        repo.client.test_connection()  # verifies the PAT actually works (else HTTP 401)
        return repo, None
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if "401" in msg:
            msg = ("Dremio rejected the token (HTTP 401). Set a valid DREMIO_TOKEN "
                   "(see the .env option in the README) and restart.")
        return None, msg


@st.cache_data(show_spinner=False)
def cached_terminals():
    repo, _ = get_repo()
    return repo.list_terminals() if repo else []


@st.cache_data(show_spinner=False)
def cached_operators(terminal):
    repo, _ = get_repo()
    return repo.list_operators(terminal) if repo else []


@st.cache_data(show_spinner=False)
def cached_services(terminal, operators):
    repo, _ = get_repo()
    return repo.list_services(terminal, tuple(operators)) if repo else []


# ---------------------------------------------------------------- shared UI
def scenario_table(defaults) -> pd.DataFrame:
    st.markdown("**Scenarios** — first row is the baseline; % is applied to Current "
                "(e.g. +0.10 = +10%). Comments are for context; you can override any rate below.")
    df = pd.DataFrame(defaults, columns=["name", "role", "pct", "comment"])
    return st.data_editor(
        df, num_rows="dynamic", use_container_width=True, key="scenario_table",
        column_config={
            "role": st.column_config.SelectboxColumn("role", options=list(ROLES)),
            "pct": st.column_config.NumberColumn("pct (+/- fraction)", format="%.4f"),
        },
    )


def render_summary(summary):
    st.subheader("Revenue simulation summary")
    frame = summary_to_frame(summary)
    st.dataframe(frame.style.format(precision=2), use_container_width=True)
    total_col = "Total Revenue (incl BCO)" if "Total Revenue (incl BCO)" in frame.columns else "Total Revenue"
    delta_col = next((c for c in frame.columns if c.startswith("Δ Revenue vs baseline")), None)
    c1, c2 = st.columns(2)
    with c1:
        st.caption(f"{total_col} by scenario")
        st.bar_chart(frame[total_col])
    with c2:
        if delta_col:
            st.caption(delta_col)
            st.bar_chart(frame[delta_col])
    with st.expander("Component breakdown"):
        st.dataframe(components_frame(summary).style.format(precision=2), use_container_width=True)
    st.download_button("Download summary CSV", frame.to_csv().encode("utf-8"),
                       file_name="revenue_simulation_summary.csv", mime="text/csv")
    for w in summary.warnings:
        st.warning(w)


def save_deal_form(summary, ctx):
    """Expander to record this simulation as a closed deal."""
    with st.expander("💾 Save as closed deal (Deal Tracker)"):
        names = [s.name for s in summary.scenarios]
        customer = st.text_input("Customer", key="deal_customer")
        c1, c2 = st.columns(2)
        chosen = c1.selectbox("Scenario the customer closed on", names, key="deal_chosen")
        cpi_opts = ["(none)"] + names
        cpi = c2.selectbox("CPI scenario (for comparison)", cpi_opts,
                           index=(cpi_opts.index("CPI") if "CPI" in names else 0), key="deal_cpi")
        notes = st.text_input("Notes", key="deal_notes")
        if st.button("Save deal", type="secondary"):
            if not customer:
                st.error("Enter a customer name.")
            else:
                deal = deals_mod.Deal(
                    customer=customer, terminal=ctx["terminal"], operator=ctx["operator"],
                    date_from=ctx["date_from"], date_to=ctx["date_to"], mode=summary.mode,
                    scenario_revenues={s.name: s.total_revenue for s in summary.scenarios},
                    chosen_scenario=chosen, baseline_scenario=summary.baseline_name,
                    cpi_scenario=None if cpi == "(none)" else cpi,
                    saved_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                    notes=notes,
                )
                store.add_deal(deal)
                st.success(f"Saved deal for {customer}.")


# ---------------------------------------------------------------- sidebar
st.sidebar.title("SL Revenue Simulator")
repo, err = get_repo()
(st.sidebar.error if err else st.sidebar.success)(
    f"Dremio not connected: {err}" if err else "Connected to Dremio")

page = st.sidebar.radio("Page", ["Simulate", "Deal Tracker"])


# ================================================================ DEAL TRACKER
if page == "Deal Tracker":
    st.header("Deal Tracker")
    from app import deals_excel
    try:
        sheets = deals_excel.load_deal_sheets()
    except FileNotFoundError:
        sheets = {}
        st.warning("`Deals Results.xlsx` not found in stage3_benchmarking_mfn/.")
    except PermissionError:
        sheets = {}
        st.error("`Deals Results.xlsx` is open in Excel — close it and refresh.")
    except Exception as e:  # noqa: BLE001
        sheets = {}
        st.error(f"Could not read Deals Results.xlsx: {e}")

    if sheets:
        tab_names = list(sheets.keys())
        for tab, sheet_name in zip(st.tabs(tab_names), tab_names):
            with tab:
                df = sheets[sheet_name]
                s = deals_excel.summarize(df)
                m = st.columns(5)
                m[0].metric("Deals", s["deals"])
                m[1].metric("Above Index", s["above_index"])
                m[2].metric("At Index", s["at_index"])
                m[3].metric("Below Index", s["below_index"])
                m[4].metric("Total actual increase", f"{s['total_actual_increase']:,.0f}")
                st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("Deals saved from simulations (this tool)"):
        saved = store.load_deals()
        if not saved:
            st.caption("None yet — run a simulation and use *Save as closed deal*.")
        else:
            agg = deals_mod.aggregate(saved)
            c = st.columns(4)
            c[0].metric("Saved deals", agg.count)
            c[1].metric("Above CPI", agg.above_cpi)
            c[2].metric("At CPI", agg.at_cpi)
            c[3].metric("Below CPI", agg.below_cpi)
            st.dataframe(pd.DataFrame(agg.rows).style.format(precision=2, na_rep="—"),
                         use_container_width=True)
            idx = st.number_input("Delete saved deal # (row index)", min_value=0,
                                  max_value=len(saved) - 1, value=0)
            if st.button("Delete selected deal"):
                store.delete_deal(int(idx))
                st.rerun()
    st.stop()


# ================================================================ SIMULATE
mode_label = st.sidebar.radio("Mode", ["Detailed Simulation", "Simple Simulation"])
mode = MODE_DETAILED if mode_label.startswith("Detailed") else MODE_SIMPLE

terminals = cached_terminals()
terminal = st.sidebar.selectbox("Terminal", terminals) if terminals else \
    st.sidebar.text_input("Terminal", "")
if terminal and repo:
    operators = st.sidebar.multiselect("Operators", cached_operators(terminal), key="ops")
    services = st.sidebar.multiselect("Services", cached_services(terminal, operators), key="svcs")
else:
    operators = [o.strip() for o in st.sidebar.text_input("Operators (comma-sep)", "").split(",") if o.strip()]
    services = [s.strip() for s in st.sidebar.text_input("Services (comma-sep)", "").split(",") if s.strip()]
col_a, col_b = st.sidebar.columns(2)
date_from = col_a.text_input("From (YYYY-MM-DD)", "2025-01-01")
date_to = col_b.text_input("To (YYYY-MM-DD)", "2025-12-31")
ctx = {"terminal": terminal, "operator": ", ".join(operators), "date_from": date_from, "date_to": date_to}

# ------------------------------------------------------------- Detailed mode
if mode == MODE_DETAILED:
    st.header("Detailed Simulation (occurrence-based)")
    scen_df = scenario_table(DEFAULT_SCENARIOS)
    scenarios = [Scenario(str(r["name"]).strip(), str(r["role"]).strip())
                 for _, r in scen_df.iterrows() if str(r.get("name", "")).strip()]
    names = [s.name for s in scenarios]
    pct_by = {str(r["name"]).strip(): float(r["pct"] or 0.0) for _, r in scen_df.iterrows()
              if str(r.get("name", "")).strip()}

    with st.expander("Occurrence types to include", expanded=False):
        oc1, oc2, oc3 = st.columns(3)
        inc_gate = oc1.checkbox("Truck & Rail gate moves", value=True)
        inc_oog = oc2.checkbox("OOG surcharge", value=True)
        inc_ot = oc3.checkbox("Overtime day-hour buckets", value=True)
    if st.button("Fetch occurrences from Dremio", disabled=repo is None):
        try:
            with st.spinner("Querying Dremio…"):
                occ = repo.get_occurrences(terminal, operators, services, date_from, date_to,
                                           include_gate=inc_gate, include_oog=inc_oog,
                                           include_overtime=inc_ot)
            st.session_state["occ"] = [
                {"item": o.item, "group": o.group, "vessel_move": o.vessel_move,
                 "occurrences": o.count, "annualized": o.annualized or 0.0} for o in occ]
        except Exception as e:  # noqa: BLE001
            st.error(f"Dremio query failed: {e}")

    occ_rows = st.session_state.get("occ") or [
        {"item": "Full-Load-40", "group": "Vessel Moves-Gateway", "vessel_move": True,
         "occurrences": 0.0, "annualized": 0.0}]
    norm = st.radio("Occurrence basis",
                    ["Current period", "Annualized", "Normalized (enter expected moves)"],
                    horizontal=True)
    occ_df = st.data_editor(pd.DataFrame(occ_rows), num_rows="dynamic",
                            use_container_width=True, key="occ_editor")
    basis = "annualized" if norm == "Annualized" else "occurrences"
    norm_target = None
    if norm.startswith("Normalized"):
        norm_target = st.number_input(
            "Expected total vessel moves (occurrences scale proportionally to this)",
            min_value=0.0, value=0.0, step=1000.0)

    st.markdown("**Current rates** — pull from the pricing system (Dremio), or upload a rate sheet")
    items_list = [str(i) for i in occ_df["item"].tolist()]
    bem_op = pricing_operator_ui(repo, terminal, operators, "d")
    if st.button("Pull current rates from Pricing (Dremio)", disabled=repo is None or not bem_op):
        try:
            with st.spinner("Querying pricing…"):
                res = repo.get_current_rates(terminal, bem_op, items_list, TODAY, is_standard_code=True)
                rates = {k: v["rate"] for k, v in res["rates"].items()}
                # OOG & overtime are surcharges applied "on top of" the Load/Discharge rate.
                base_ld = _representative_ld_rate(rates)
                oog_res = repo.get_oog_surcharge(terminal, bem_op, base_ld, TODAY, is_standard_code=True)
                if oog_res["oog"]:
                    rates[OOG_ITEM] = oog_res["oog"]["rate"]
                ot_inds = [it for it in items_list if parse_overtime_indicator(it)]
                ot_res = repo.get_overtime_rates(terminal, bem_op, ot_inds, base_ld, TODAY,
                                                 is_standard_code=True)
                rates.update({ind: r["rate"] for ind, r in ot_res["rates"].items()})
            st.session_state["px_rates"] = rates
            st.session_state["px_sheet"] = res["sheet"]
            extra = []
            if oog_res["oog"]:
                extra.append("OOG")
            if ot_res["rates"]:
                extra.append(f"{len(ot_res['rates'])} overtime bands")
            st.success(f"Pulled {len(res['rates'])} current rates for {bem_op}"
                       + (f" (+ {', '.join(extra)})" if extra else "") + ".")
        except Exception as e:  # noqa: BLE001
            st.error(f"Pricing pull failed: {e}")
    show_sheet_info(st.session_state.get("px_sheet"))
    px = st.session_state.get("px_rates", {})

    up_d = st.file_uploader("…or upload a rate sheet (CSV/XLSX) → Current", type=["csv", "xlsx"],
                            key="ratesheet_detailed")
    parsed_d = {}
    if up_d is not None:
        raw_d = pd.read_csv(up_d) if up_d.name.lower().endswith(".csv") else pd.read_excel(up_d)
        cols_d = list(raw_d.columns)
        d1, d2 = st.columns(2)
        icol = d1.selectbox("Item column", cols_d, key="d_item_col")
        rcol = d2.selectbox("Rate column", cols_d, index=min(1, len(cols_d) - 1), key="d_rate_col")
        parsed_d = parse_rate_sheet_by_item(raw_d, icol, rcol, items_list)
        st.caption(f"Matched {len(parsed_d)} of {len(items_list)} items.")

    st.markdown("**Rates per item × scenario** — Current from pricing/upload; others derive as "
                "Current×(1+%); edit any cell to override")
    first = names[0] if names else "Current"
    rate_df = pd.DataFrame({"item": occ_df["item"]})
    current_vals = [float(px.get(it, parsed_d.get(it, 0.0))) for it in items_list]
    for n in names:
        rate_df[n] = [c * (1.0 + pct_by.get(n, 0.0)) for c in current_vals]
    rate_df["BCO per occurrence (USD)"] = 0.0
    st.caption("Tip: enter **BCO per occurrence (USD)** to include BCO revenue "
               "(occurrences × this). The summary shows totals with and without BCO.")
    rate_df = st.data_editor(rate_df, use_container_width=True, num_rows="dynamic",
                             key="rate_editor_detailed")

    c1, c2 = st.columns(2)
    roe = c1.number_input("RoE (rates→results)", value=1.0, min_value=0.0001)
    if repo and c2.button("Pull variable cost/move (Cost_OS)", disabled=not terminal):
        try:
            v = repo.get_variable_cpm(terminal)
            st.session_state["var_cpm"] = -abs(v) if v is not None else None
            if v is None:
                st.warning("No 'Variable CPM' found for this terminal in Cost_OS.")
            else:
                st.success(f"Variable CPM pulled: {v:,.2f} → applied as {-abs(v):,.2f}/move.")
        except Exception as e:  # noqa: BLE001
            st.error(f"Cost pull failed: {e}")
    default_vc = st.session_state.get("var_cpm")
    var_cost = st.number_input("Variable cost / move (negative)",
                               value=float(default_vc) if default_vc is not None else -32.0)
    include_bco = True  # BCO always computed; summary shows with & without

    if st.button("Run detailed simulation", type="primary"):
        occ_lookup = {r["item"]: r for _, r in occ_df.iterrows()}
        # normalized basis: scale so total vessel-move occurrences hit the target
        factor = 1.0
        if norm_target and norm_target > 0:
            cur_total = sum(float(o.get(basis, 0.0) or 0.0) for _, o in occ_df.iterrows()
                            if bool(o.get("vessel_move", True)))
            factor = (norm_target / cur_total) if cur_total else 1.0
        items = []
        for _, rr in rate_df.iterrows():
            o = occ_lookup.get(rr["item"], {})
            items.append(PmsItem(
                group=str(o.get("group", "")), item=str(rr["item"]),
                occurrences=float(o.get(basis, 0.0) or 0.0) * factor,
                rates={n: float(rr.get(n, 0.0) or 0.0) for n in names},
                vessel_move=bool(o.get("vessel_move", True)),
                bco_rate=float(rr.get("BCO per occurrence (USD)", 0.0) or 0.0)))
        summary = run_detailed(items, scenarios, roe=roe, var_cost_per_move=var_cost,
                               include_bco=include_bco, baseline_name=names[0])
        st.session_state["last_summary"] = summary
        st.session_state["sl_per_occ"] = {"rows": sl_revenue_per_item(items, names, roe),
                                          "scenarios": names}

# ------------------------------------------------------------- Simple mode
else:
    st.header("Simple Simulation (share-based)")

    # 1) Volume + shares (prefill from Dremio)
    cc = st.columns([1, 1, 2])
    if repo and cc[0].button("Prefill volume + shares from Dremio"):
        try:
            with st.spinner("Querying Dremio…"):
                sh = repo.get_shares(terminal, operators, services, date_from, date_to)
            st.session_state["vol"] = sh.get("_top_moves", 0.0)
            st.session_state["shares"] = {k: sh[k] for k in SHARE_KEYS if k in sh}
        except Exception as e:  # noqa: BLE001
            st.error(f"Dremio query failed: {e}")
    volume = cc[1].number_input("Annual volume (moves)", value=float(st.session_state.get("vol", 100000.0)))

    st.markdown("**Move-type shares** (share = category moves ÷ total; `reefer_dwell` is days)")
    default_shares = st.session_state.get("shares", {
        "full_ld": 0.22, "empty_ld": 0.01, "transhipment": 0.74, "shift": 0.03,
        "gate_full": 0.22, "gate_empty": 0.01, "reefer": 0.014, "reefer_dwell": 6.0,
        "oog": 0.012, "imo": 0.0029})
    shares_df = st.data_editor(
        pd.DataFrame({"key": SHARE_KEYS, "value": [float(default_shares.get(k, 0.0)) for k in SHARE_KEYS]}),
        use_container_width=True, key="shares_editor", hide_index=True)
    shares = {r["key"]: float(r["value"]) for _, r in shares_df.iterrows()}

    # 2) Current rates — pull from pricing, upload a rate sheet, or enter manually
    st.markdown("**Current rates** — pull from pricing (Dremio), upload a rate sheet, or type them")
    bem_op_s = pricing_operator_ui(repo, terminal, operators, "s")
    if st.button("Pull current rates from Pricing (Dremio)", disabled=repo is None or not bem_op_s):
        try:
            with st.spinner("Querying pricing…"):
                res = repo.get_current_rates(terminal, bem_op_s, list(SIMPLE_LINE_KEYS.values()),
                                             TODAY, is_standard_code=True)
            keyrate = {k: v["rate"] for k, v in res["rates"].items()}
            st.session_state["px_simple"] = {line: keyrate.get(key) for line, key in SIMPLE_LINE_KEYS.items()
                                             if keyrate.get(key) is not None}
            st.session_state["px_sheet_s"] = res["sheet"]
            st.success(f"Pulled current rates for {bem_op_s}.")
        except Exception as e:  # noqa: BLE001
            st.error(f"Pricing pull failed: {e}")
    show_sheet_info(st.session_state.get("px_sheet_s"))
    px_s = st.session_state.get("px_simple", {})
    up = st.file_uploader("…or upload a rate sheet (CSV/XLSX)", type=["csv", "xlsx"])
    parsed = {}
    if up is not None:
        raw = pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
        cols = list(raw.columns)
        u1, u2 = st.columns(2)
        item_col = u1.selectbox("Item column", cols)
        rate_col = u2.selectbox("Rate column", cols, index=min(1, len(cols) - 1))
        parsed = parse_rate_sheet(raw, item_col, rate_col)
        st.caption(f"Matched {len(parsed)} of {len(SIMPLE_LINES)} lines: {parsed}")
    cur_df = st.data_editor(
        pd.DataFrame({"line": SIMPLE_LINES,
                      "current rate": [float(px_s.get(l, parsed.get(l, 0.0))) for l in SIMPLE_LINES]}),
        use_container_width=True, key="current_rates_editor", hide_index=True)
    current = {r["line"]: float(r["current rate"]) for _, r in cur_df.iterrows()}

    # 3) Scenarios (name, role, pct, comment)
    scen_df = scenario_table(DEFAULT_SCENARIOS)
    scenarios = [Scenario(str(r["name"]).strip(), str(r["role"]).strip())
                 for _, r in scen_df.iterrows() if str(r.get("name", "")).strip()]
    names = [s.name for s in scenarios]
    pct_by = {str(r["name"]).strip(): float(r["pct"] or 0.0) for _, r in scen_df.iterrows()
              if str(r.get("name", "")).strip()}

    # derived rate preview + optional overrides
    derived = {n: derive_from_pct(current, pct_by.get(n, 0.0)) for n in names}
    with st.expander("Rate overrides (blank = use derived Current×(1+%))"):
        ov_df = pd.DataFrame({"line": SIMPLE_LINES})
        for n in names:
            ov_df[n] = pd.NA
        ov_df = st.data_editor(ov_df, use_container_width=True, key="override_editor", hide_index=True)
        for _, rr in ov_df.iterrows():
            for n in names:
                v = rr.get(n)
                if pd.notna(v) and str(v).strip() != "":
                    derived[n][rr["line"]] = float(v)

    st.caption("Resulting rates per line × scenario")
    st.dataframe(pd.DataFrame(derived).rename_axis("line"), use_container_width=True)

    ok, msgs = validate_ordering(derived, "Floor", "Current", "Target") if {"Floor", "Current", "Target"} <= set(names) else (True, [])
    if not ok:
        st.warning("Floor ≤ Current ≤ Target violated: " + "; ".join(msgs[:5]))

    # 4) Per-scenario assumptions
    st.markdown("**Per-scenario assumptions**")
    assume = pd.DataFrame({
        "scenario": names, "overtime %": [0.0] * len(names), "rebate rate": [0.0] * len(names),
        "oog surcharge": [1.0] * len(names), "imo surcharge": [0.5] * len(names),
        "storage (total)": [0.0] * len(names), "empty pool (total)": [0.0] * len(names)})
    assume = st.data_editor(assume, use_container_width=True, key="assume_editor", hide_index=True)

    def _col(c):
        return {r["scenario"]: float(r[c] or 0.0) for _, r in assume.iterrows()}

    if st.button("Run simple simulation", type="primary"):
        rates = {line: {n: derived[n].get(line, 0.0) for n in names} for line in SIMPLE_LINES}
        inp = SimpleInputs(
            volume=volume, scenarios=scenarios, shares=shares, rates=rates,
            overtime_pct=_col("overtime %"), rebate_rate=_col("rebate rate"),
            oog_mult=_col("oog surcharge"), imo_mult=_col("imo surcharge"),
            storage=_col("storage (total)"), empty_pool=_col("empty pool (total)"),
            baseline_name=names[0])
        st.session_state["last_summary"] = run_simple(inp)
        st.session_state["sl_per_occ"] = None  # per-occurrence view is detailed-mode only

# ------------------------------------------------------------- output
summary = st.session_state.get("last_summary")
if summary is not None:
    names = [s.name for s in summary.scenarios]
    default_ix = names.index(summary.baseline_name) if summary.baseline_name in names else 0
    baseline_choice = st.selectbox("Baseline scenario (deltas are measured against this)",
                                   names, index=default_ix, key="baseline_choice")
    if baseline_choice != summary.baseline_name:
        summary = finalize_summary(summary.mode, summary.scenarios, baseline_choice, summary.warnings)
    render_summary(summary)

    sp = st.session_state.get("sl_per_occ")
    if sp and sp.get("rows"):
        st.subheader("SL Revenue per Occurrence")
        st.caption("Per-item revenue = occurrences × rate ÷ RoE (matches the workbook tab).")
        per_df = pd.DataFrame(sp["rows"])
        # append a totals row across the numeric columns
        num_cols = ["Occurrences", *sp["scenarios"]]
        totals = {c: per_df[c].sum() for c in num_cols if c in per_df.columns}
        totals.update({"Item #": "", "Group": "", "Item": "TOTAL", "Vessel Move?": ""})
        per_df = pd.concat([per_df, pd.DataFrame([totals])], ignore_index=True)
        st.dataframe(per_df.style.format(precision=2, na_rep=""), use_container_width=True,
                     hide_index=True)
        st.download_button("Download SL revenue per occurrence (CSV)",
                           per_df.to_csv(index=False).encode("utf-8"),
                           file_name="sl_revenue_per_occurrence.csv", mime="text/csv")

    save_deal_form(summary, ctx)
