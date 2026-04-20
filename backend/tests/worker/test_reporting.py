from __future__ import annotations

import pytest

from app.modules.evaluations import lifecycle
from app.worker import reporting


pytestmark = pytest.mark.worker


def test_reporting_module_reexports_lifecycle_helpers() -> None:
    expected_exports = {
        "build_report_summary": lifecycle.build_report_summary,
        "finalize_run": lifecycle.finalize_run,
        "mark_run_failed": lifecycle.mark_run_failed,
        "reconcile_expired_paused_runs": lifecycle.reconcile_expired_paused_runs,
        "reconcile_run_timeout": lifecycle.reconcile_run_timeout,
        "upsert_report": lifecycle.upsert_report,
    }

    assert set(reporting.__all__) == set(expected_exports)
    for name, function in expected_exports.items():
        assert getattr(reporting, name) is function

