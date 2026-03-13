"""Root conftest for labs — handles per-lab sys.path isolation.

Each lab has modules with identical names (app, db, models). When running
all labs' tests together (`pytest`), we need to ensure each lab imports
from its own directory.

Strategy: before each test, ensure the test's lab directory is at
sys.path[0] and clear any cached modules that could be from another lab.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Module names that exist in multiple labs — must be cleared between labs
_SHARED_NAMES = {
    "app", "db", "models", "crypto", "test_helpers", "state_machine",
    "ledger", "reconciler", "resilient_client", "metrics",
    "event_store", "read_model", "producer", "consumer",
    "provider", "client", "schemas", "rate_limiter",
    "rule_engine", "pipeline", "settlement",
    "test_payments", "test_webhooks", "test_crypto", "test_state_machine",
    "test_ledger", "test_reconciler", "test_resilient_client", "test_k8s",
    "test_monitoring", "test_settlement", "test_event_store",
    "test_contracts", "test_rate_limiter", "test_terraform",
    "test_rule_engine", "test_kyc_app", "test_kyc_pipeline",
}

_active_lab: str | None = None


@pytest.fixture(autouse=True)
def _isolate_lab_imports(request: pytest.FixtureRequest) -> None:
    """Ensure each test imports from its own lab directory."""
    global _active_lab
    test_file = Path(str(request.fspath))
    lab_dir = str(test_file.parent)

    if lab_dir == _active_lab:
        return

    # Evict modules from previous lab
    for name in list(sys.modules):
        if name in _SHARED_NAMES:
            del sys.modules[name]

    # Remove previous lab from sys.path
    if _active_lab and _active_lab in sys.path:
        sys.path.remove(_active_lab)

    # Push current lab to front of sys.path
    if lab_dir in sys.path:
        sys.path.remove(lab_dir)
    sys.path.insert(0, lab_dir)

    _active_lab = lab_dir
