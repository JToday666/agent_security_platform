from __future__ import annotations

from pathlib import Path

from tests.helpers.scripts import load_module_from_path


def test_patch_html_file_adds_non_blocking_sandbox_warning_overlay(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_sandbox_warning_overlay_interaction_under_test",
        backend_root
        / "scripts"
        / "datasets"
        / "patch_eia_sandbox_warning_overlay_interaction.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        """
<html><body class="sandbox-agent-warning-lock">
<button id="completeActionButton" type="button">Disable paging</button>
<div id="sandbox-agent-warning-overlay" aria-modal="true" role="dialog">
  <div id="sandbox-agent-warning-modal">
    <button id="sandbox-agent-warning-button" type="button">Continue in sandbox</button>
  </div>
</div>
</body></html>
""",
        encoding="utf-8",
    )

    assert module.patch_html_file(html_path)
    text = html_path.read_text(encoding="utf-8")
    assert 'id="eia-sandbox-warning-interaction-patch"' in text
    assert 'id="eia-sandbox-warning-nonblocking-style"' in text
    assert "eia-sandbox-warning-interaction-patch-v1" in text
    assert "closeSandboxWarningFromTaskInteraction" in text
    assert "eia_sandbox_warning_closed" in text
    assert "sandbox-agent-warning-button" in text
    assert "Disable paging" in text
    assert not module.patch_html_file(html_path)


def test_patch_html_file_skips_pages_without_sandbox_warning_overlay(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_sandbox_warning_overlay_interaction_under_test_skip",
        backend_root
        / "scripts"
        / "datasets"
        / "patch_eia_sandbox_warning_overlay_interaction.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text("<html><body><button>Submit</button></body></html>", encoding="utf-8")

    assert not module.patch_html_file(html_path)
    assert "eia-sandbox-warning-interaction-patch" not in html_path.read_text(
        encoding="utf-8"
    )
