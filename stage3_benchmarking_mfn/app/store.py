"""Local JSON persistence for closed-deal records (Deal Tracker).

Stored next to the app in ``deal_records.json`` (gitignored). Small scale — the
whole file is read/written each time, which is fine for a pricing team's volume.
"""
from __future__ import annotations

import json
from pathlib import Path

from engine.deals import Deal

STORE_PATH = Path(__file__).resolve().parents[1] / "deal_records.json"


def load_deals(path: Path | None = None) -> list[Deal]:
    p = path or STORE_PATH
    if not p.exists():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [Deal.from_dict(d) for d in raw]


def save_deals(deals, path: Path | None = None) -> None:
    p = path or STORE_PATH
    p.write_text(json.dumps([d.to_dict() for d in deals], indent=2), encoding="utf-8")


def add_deal(deal: Deal, path: Path | None = None) -> list[Deal]:
    deals = load_deals(path)
    deals.append(deal)
    save_deals(deals, path)
    return deals


def delete_deal(index: int, path: Path | None = None) -> list[Deal]:
    deals = load_deals(path)
    if 0 <= index < len(deals):
        deals.pop(index)
        save_deals(deals, path)
    return deals
