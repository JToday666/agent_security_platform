from __future__ import annotations

from pathlib import Path

from tests.helpers.scripts import load_module_from_path


def test_patch_html_file_records_b3_normal_completion_event(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_b3_normal_completion_events_under_test",
        backend_root
        / "scripts"
        / "datasets"
        / "patch_eia_b3_normal_completion_events.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        """
<html><body>
<button data-eia-normal-complete="1" type="button">Get Receipt</button>
<script id="eia-b3-normal-fix-script">
(function(){
  if (window.__EIA_B3_NORMAL_FIX_V2__) return;
  window.__EIA_B3_NORMAL_FIX_V2__ = true;
  function showDone(){}
  function stopEvent(e){ return false; }
  function normalizeControl(el){
    if(!el) return;
    try{ el.disabled = false; }catch(_e){}
  }
  function handleComplete(control, e){
    normalizeControl(control);
    showDone();
    return stopEvent(e);
  }
})();
</script>
</body></html>
""",
        encoding="utf-8",
    )

    assert module.patch_html_file(html_path)
    text = html_path.read_text(encoding="utf-8")
    assert "eia-b3-normal-completion-events-v1" in text
    assert "recordNormalCompletion(control" in text
    assert "submit_button_click" in text
    assert "legitimate_final_action_triggered" in text
    assert "legitimate-final-action" in text
    assert "showDone();" in text
    assert not module.patch_html_file(html_path)


def test_patch_html_file_skips_pages_without_b3_normal_fix(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_b3_normal_completion_events_under_test_skip",
        backend_root
        / "scripts"
        / "datasets"
        / "patch_eia_b3_normal_completion_events.py",
    )
    html_path = tmp_path / "sample.html"
    html_path.write_text("<html><body><button>Get Receipt</button></body></html>", encoding="utf-8")

    assert not module.patch_html_file(html_path)
    assert "eia-b3-normal-completion-events-v1" not in html_path.read_text(
        encoding="utf-8"
    )


def test_patch_html_text_raises_for_unknown_normal_fix_shape(
    backend_root: Path,
) -> None:
    module = load_module_from_path(
        "patch_eia_b3_normal_completion_events_under_test_bad_shape",
        backend_root
        / "scripts"
        / "datasets"
        / "patch_eia_b3_normal_completion_events.py",
    )

    html = """
<script id="eia-b3-normal-fix-script">
(function(){
  if (window.__EIA_B3_NORMAL_FIX_V2__) return;
})();
</script>
"""

    try:
        module.patch_html_text(html)
    except ValueError as exc:
        assert "unsupported eia-b3-normal-fix-script shape" in str(exc)
    else:
        raise AssertionError("expected unsupported script shape to fail")
