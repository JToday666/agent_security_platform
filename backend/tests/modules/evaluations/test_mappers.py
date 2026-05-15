from __future__ import annotations

from app.modules.evaluations.application.mappers import build_status_text
from app.platform.i18n import set_current_locale


def test_build_status_text_uses_current_locale() -> None:
    token = set_current_locale("en-US")
    try:
        assert (
            build_status_text("pending", None)
            == "The task has been created and is waiting to start."
        )
        assert build_status_text("running", None) == "The task is running."
        assert build_status_text("running", "A1") == "Currently evaluating dataset A1."
        assert build_status_text("failed", None) == "Evaluation failed."
    finally:
        token.reset()
