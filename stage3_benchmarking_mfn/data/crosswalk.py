"""Operational crosswalk config for the pricing pull (approved via reference/crosswalk_draft.json).

* TERMINAL_OVERRIDES  - fixes gaps in Lookups.Terminal_mapping (e.g. Vado2).
* QUAY_INCLUDE_ACTIVITIES - the load/discharge quay-move family to pull from BEM.
* CUSTOMER_HINTS      - TOS operator code -> BEM.Customer brand, to AUTO-SUGGEST the
                        right pricing customer (BEM uses 59 brand names that the RM
                        Customer_mapping lookup does not fully cover). The app still lets
                        the manager pick/override from the BEM customers at the terminal.
"""
from __future__ import annotations

# TOS terminal -> Standard_Terminal override (applied before the Lookups join).
TERMINAL_OVERRIDES = {
    "Vado2": "Vado Gateway Terminal (APM Terminals)",
}

# BEM activity_name values treated as the quayside per-move charge (no global-catalogue check).
QUAY_INCLUDE_ACTIVITIES = [
    "Load or Discharge Move", "Load or Discharge Move excl Yard Move",
    "Load Move", "Discharge Move",
    "Gateway Cycle Move", "Gateway Cycle Move - Import", "Gateway Cycle Move - Export",
    "Throughput Move (Standard Lift)",
    "Transshipment Move", "Transshipment Move - Premium Service",
    "Load or Discharge Move - Premium Service", "Load or Discharge Move - Cabotage (coastal)",
    "Cabotage (coastal) - Load or Discharge Move", "Load or Discharge Move - Bundled Platform or Flat rack",
    "Restow Move - via Quay", "Restow Move - Cell to Cell",
    "Restow Move - Via Quay - Premium Service", "Restow Move - Cell to Cell - Premium Service",
]

# BEM activity_name values for landside gate legs (Truck/Rail), category_name='Gate Operations'
# (a separate category from quay ops — see QUAY_INCLUDE_ACTIVITIES above).
GATE_INCLUDE_ACTIVITIES = [
    "Gate Move Truck", "Gate Move Truck - Additional", "Gate Move Truck - Export",
    "Gate Move Truck - Import", "Gate Move Truck - Import - Cabotage (Coastal)",
    "Gate Move Rail",
]

# TOS operator code -> BEM.Customer brand (auto-suggestion only; overridable in the UI).
CUSTOMER_HINTS = {
    "MAE": "MAERSK", "MAEU": "MAERSK", "MSK": "MAERSK",
    "MSC": "MSC", "MSCU": "MSC",
    "CMA": "CMA-CGM", "CGM": "CMA-CGM", "CMD": "CMA-CGM",
    "HLC": "HAPAG",
    "ONE": "ONE",
    "HMM": "HMM",
    "COS": "COSCO", "COSC": "COSCO", "COSXX": "COSCO",
    "EVG": "EVERGREEN", "EVE": "EVERGREEN",
    "OOL": "OOCL", "OOCL": "OOCL", "OOC": "OOCL",
    "YML": "YANG MING", "YMJ": "YANG MING", "YMP": "YANG MING", "YM": "YANG MING",
    "ZIM": "ZIM",
    "PIL": "PIL",
    "ARK": "ARKAS", "ARKAS": "ARKAS",
    "XCL": "X-PRESS FEEDER", "XPF": "X-PRESS FEEDER",
    "UF6": "UNIFEEDER", "UFE": "UNIFEEDER", "UFS": "UNIFEEDER",
    "WEC": "WEST EUROPEAN CONTAINER LINE",
    "SAM": "SAMSKIP",
    "TUR": "TURKON",
    "MRF": "MARFET",
    "BOR": "BORCHARD LINE",
    "BOL": "BOLUDA LINES", "BOLL": "BOLUDA LINES",
    "EIM": "EIMSKIP",
    "LOG": "LOGIN", "LOGIN": "LOGIN",
    "ACL": "ATLANTIC CONTAINER LINE",
    "MDV": "MEDKON LINES",
    "SCI": "SCI",
}


def suggest_customer(tos_operator_code):
    return CUSTOMER_HINTS.get(str(tos_operator_code).strip().upper())
