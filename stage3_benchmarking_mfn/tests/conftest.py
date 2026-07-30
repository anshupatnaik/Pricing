"""Test fixtures + path setup (engine tests run without Dremio or network)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def hapag_fixture():
    return json.loads((FIXTURES / "hapag_vado.json").read_text())


@pytest.fixture(scope="session")
def pms_fixture():
    return json.loads((FIXTURES / "pms_parity.json").read_text())
