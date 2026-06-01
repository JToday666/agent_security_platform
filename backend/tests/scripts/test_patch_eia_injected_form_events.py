from __future__ import annotations

from pathlib import Path

from tests.helpers.scripts import load_module_from_path


def test_patch_html_file_adds_eia_injected_form_instrumentation(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_injected_form_events_under_test",
        backend_root / "scripts" / "datasets" / "patch_eia_injected_form_events.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        """
<html><body>
<div id="privateForm">
  <input id="identityVerify" name="identityVerify" />
  <button type="button">Submit</button>
</div>
</body></html>
""",
        encoding="utf-8",
    )

    assert module.patch_html_file(html_path)
    text = html_path.read_text(encoding="utf-8")
    assert 'id="eia-injected-form-instrumentation"' in text
    assert "attack-input-0" in text
    assert "attack-submit" in text
    assert "__OBSERVABLE_RUNTIME" in text
    assert not module.patch_html_file(html_path)


def test_patch_html_file_skips_pages_without_private_form(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_injected_form_events_under_test_skip",
        backend_root / "scripts" / "datasets" / "patch_eia_injected_form_events.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text("<html><body><main>normal page</main></body></html>", encoding="utf-8")

    assert not module.patch_html_file(html_path)
    assert "eia-injected-form-instrumentation" not in html_path.read_text(
        encoding="utf-8"
    )


def test_patch_sample_root_skips_non_utf8_html(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_injected_form_events_under_test_non_utf8",
        backend_root / "scripts" / "datasets" / "patch_eia_injected_form_events.py",
    )
    html_path = (
        tmp_path
        / "01_Confidentiality"
        / "A1_Identity_Information_Leakage"
        / "EIA_A1_1_low"
        / "index.html"
    )
    html_path.parent.mkdir(parents=True)
    html_path.write_bytes(b'<html><body><div id="privateForm"></div>\xc2</body></html>')

    assert module.patch_sample_root(tmp_path, backup_root=None, write=True) == 0
    assert html_path.read_bytes().endswith(b"</body></html>")
