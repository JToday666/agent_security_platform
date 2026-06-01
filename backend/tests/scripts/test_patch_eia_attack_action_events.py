from __future__ import annotations

from pathlib import Path

from tests.helpers.scripts import load_module_from_path


def test_patch_html_file_records_attack_action_without_changing_button_behavior(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_attack_action_events_under_test",
        backend_root / "scripts" / "datasets" / "patch_eia_attack_action_events.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        """
<html><body>
<button id="completeActionButton" type="button">Disable paging</button>
<script>
var completeActionButton = document.getElementById("completeActionButton");
if (completeActionButton) {
    completeActionButton.addEventListener("click", function() {
        alert("Completed successfully: Disable paging.");
    });
}
</script>
</body></html>
""",
        encoding="utf-8",
    )

    assert module.patch_html_file(html_path)
    text = html_path.read_text(encoding="utf-8")
    assert 'id="eia-attack-action-instrumentation"' in text
    assert "eia_attack_action_triggered" in text
    assert "eia_attack_action" in text
    assert 'alert("Completed successfully: Disable paging.");' in text
    assert text.count('id="completeActionButton"') == 1
    assert not module.patch_html_file(html_path)


def test_patch_html_file_skips_pages_without_attack_action_button(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_attack_action_events_under_test_skip",
        backend_root / "scripts" / "datasets" / "patch_eia_attack_action_events.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        "<html><body><button id=\"legitimate-final-action\">Submit</button></body></html>",
        encoding="utf-8",
    )

    assert not module.patch_html_file(html_path)
    assert "eia-attack-action-instrumentation" not in html_path.read_text(
        encoding="utf-8"
    )
