"""Load the existing 'Deals Results.xlsx' tracker for the Deal Tracker page.

The workbook has per-year 'Deals <year>' sheets with columns: Terminal, Region,
Customer, Status, Effective Date, Initial Revenue, Anchor/Target/Floor/Index/Actual %,
their Revenue and Increase columns, Actual-vs-{Anchor,Target,Floor,Index}, Remarks, Moves.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DEALS_XLSX = Path(__file__).resolve().parents[1] / "Deals Results.xlsx"


def load_deal_sheets(path: Path | None = None) -> dict:
    """Return {sheet_name: DataFrame} for every 'Deals <year>' sheet.

    Raises the underlying error (e.g. PermissionError if the file is open in
    Excel, FileNotFoundError if missing) so the caller can show a message.
    """
    p = path or DEALS_XLSX
    xls = pd.ExcelFile(p)  # engine=openpyxl for .xlsx
    out = {}
    for sheet in xls.sheet_names:
        if sheet.lower().startswith("deals"):
            df = xls.parse(sheet)
            df = df.dropna(how="all")
            out[sheet] = df
    return out


def summarize(df: pd.DataFrame) -> dict:
    """Headline metrics for a deals sheet: counts, revenue, and Actual-vs-Index."""
    def col(name):
        return df[name] if name in df.columns else pd.Series(dtype="float64")

    vs_index = pd.to_numeric(col("Actual vs Index"), errors="coerce").dropna()
    actual_increase = pd.to_numeric(col("Actual Increase"), errors="coerce").dropna()
    actual_rev = pd.to_numeric(col("Actual Revenue"), errors="coerce").dropna()
    return {
        "deals": int(len(df)),
        "closed": int((col("Status").astype(str).str.lower() == "closed").sum()),
        "above_index": int((vs_index > 0).sum()),
        "at_index": int((vs_index == 0).sum()),
        "below_index": int((vs_index < 0).sum()),
        "total_actual_revenue": float(actual_rev.sum()),
        "total_actual_increase": float(actual_increase.sum()),
    }
