from __future__ import annotations

from pathlib import Path

from tests.helpers.scripts import load_module_from_path


def test_patch_html_file_adds_non_blocking_task_reminder_instrumentation(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_task_reminder_interaction_under_test",
        backend_root / "scripts" / "datasets" / "patch_eia_task_reminder_interaction.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        """
<html><body>
<div id="agent-task-reminder-overlay">
  <button id="agent-task-reminder-button">Continue</button>
</div>
<form><input id="lastName" /></form>
</body></html>
""",
        encoding="utf-8",
    )

    assert module.patch_html_file(html_path)
    text = html_path.read_text(encoding="utf-8")
    assert 'id="eia-task-reminder-interaction-patch"' in text
    assert 'id="eia-task-reminder-nonblocking-style"' in text
    assert "task-reminder-continue" in text
    assert "closeReminderFromTaskInteraction" in text
    assert "scheduleAutoClose" in text
    assert "eiaTaskReminderAutoDismiss" in text
    assert not module.patch_html_file(html_path)


def test_patch_html_file_skips_pages_without_task_reminder(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_task_reminder_interaction_under_test_skip",
        backend_root / "scripts" / "datasets" / "patch_eia_task_reminder_interaction.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text("<html><body><form></form></body></html>", encoding="utf-8")

    assert not module.patch_html_file(html_path)
    assert "eia-task-reminder-interaction-patch" not in html_path.read_text(
        encoding="utf-8"
    )


def test_patch_html_file_upgrades_existing_task_reminder_patch(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_task_reminder_interaction_under_test_upgrade",
        backend_root / "scripts" / "datasets" / "patch_eia_task_reminder_interaction.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        """
<html><body>
<div id="agent-task-reminder-overlay">
  <button id="agent-task-reminder-button">Continue</button>
</div>
<script id="eia-task-reminder-interaction-patch">
(function() {
  function closeReminderFromTaskInteraction() {}
})();
</script>
</body></html>
""",
        encoding="utf-8",
    )

    assert module.patch_html_file(html_path)
    text = html_path.read_text(encoding="utf-8")
    assert text.count('id="eia-task-reminder-interaction-patch"') == 1
    assert 'id="eia-task-reminder-nonblocking-style"' in text
    assert "scheduleAutoClose" in text
    assert "setTimeout(closeTimer" in text
