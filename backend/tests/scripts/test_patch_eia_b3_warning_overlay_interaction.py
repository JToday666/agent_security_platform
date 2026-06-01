from __future__ import annotations

from pathlib import Path

from tests.helpers.scripts import load_module_from_path


def test_patch_html_file_adds_non_blocking_warning_overlay_instrumentation(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_b3_warning_overlay_interaction_under_test",
        backend_root
        / "scripts"
        / "datasets"
        / "patch_eia_b3_warning_overlay_interaction.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        """
<html><body>
<form><input id="lastName" /></form>
<div id="agent-warning-overlay" aria-modal="true" role="dialog">
  <div id="agent-warning-panel">
    <button id="agent-warning-close" aria-label="Close this notice" type="button">x</button>
    <p>Injected warning stays visible initially.</p>
  </div>
</div>
</body></html>
""",
        encoding="utf-8",
    )

    assert module.patch_html_file(html_path)
    text = html_path.read_text(encoding="utf-8")
    assert 'id="eia-b3-warning-interaction-patch"' in text
    assert 'id="eia-b3-warning-nonblocking-style"' in text
    assert "eia-b3-warning-interaction-patch-v1" in text
    assert "closeWarningFromTaskInteraction" in text
    assert "scheduleAutoClose" in text
    assert "eia_b3_warning_closed" in text
    assert "agent-warning-close" in text
    assert "Injected warning stays visible initially." in text
    assert not module.patch_html_file(html_path)


def test_patch_html_file_skips_pages_without_warning_overlay(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_b3_warning_overlay_interaction_under_test_skip",
        backend_root
        / "scripts"
        / "datasets"
        / "patch_eia_b3_warning_overlay_interaction.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text("<html><body><form></form></body></html>", encoding="utf-8")

    assert not module.patch_html_file(html_path)
    assert "eia-b3-warning-interaction-patch" not in html_path.read_text(
        encoding="utf-8"
    )


def test_patch_html_file_upgrades_existing_warning_overlay_patch(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_b3_warning_overlay_interaction_under_test_upgrade",
        backend_root
        / "scripts"
        / "datasets"
        / "patch_eia_b3_warning_overlay_interaction.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        """
<html><body>
<div id="agent-warning-overlay" aria-modal="true" role="dialog">
  <div id="agent-warning-panel">
    <button id="agent-warning-close" aria-label="Close this notice" type="button">x</button>
  </div>
</div>
<script id="eia-b3-warning-interaction-patch">
(function() {
  function closeWarningFromTaskInteraction() {}
})();
</script>
</body></html>
""",
        encoding="utf-8",
    )

    assert module.patch_html_file(html_path)
    text = html_path.read_text(encoding="utf-8")
    assert text.count('id="eia-b3-warning-interaction-patch"') == 1
    assert 'id="eia-b3-warning-nonblocking-style"' in text
    assert "scheduleAutoClose" in text
    assert "setTimeout(closeTimer" in text
