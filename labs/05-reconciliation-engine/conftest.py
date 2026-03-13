"""Test fixtures for reconciliation engine lab."""

from __future__ import annotations

import sys
from pathlib import Path

# Collection-time isolation: clear cached modules from other labs
_lab_dir = str(Path(__file__).parent)
_shared = {
    "app", "db", "models", "crypto", "test_helpers", "state_machine",
    "ledger", "reconciler", "resilient_client", "metrics",
    "event_store", "read_model", "producer", "consumer",
    "provider", "client", "schemas", "rate_limiter",
    "rule_engine", "pipeline", "settlement",
}
for _name in list(sys.modules):
    if _name in _shared:
        del sys.modules[_name]
if _lab_dir in sys.path:
    sys.path.remove(_lab_dir)
sys.path.insert(0, _lab_dir)
