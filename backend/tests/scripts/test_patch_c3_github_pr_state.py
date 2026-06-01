from __future__ import annotations

from pathlib import Path

from tests.helpers.scripts import load_module_from_path


def _load_module(backend_root: Path):
    return load_module_from_path(
        "patch_c3_github_pr_state_under_test",
        backend_root / "scripts" / "datasets" / "patch_c3_github_pr_state.py",
    )


def _c3_browser_art_js() -> str:
    return """
(function () {
  function currentState(runtime, extra) {
    const c3 = runtime.c3Browser || {};
    const editorText = readEditorText();
    return Object.assign(
      {
        family_id: "Browser-art_C3_github_pr",
        site_family: "github_pr",
        edited: Boolean(c3.edited),
        commit_clicked: Boolean(c3.commitClicked),
        final_code_excerpt: String(editorText || "").slice(0, 1200),
        code_length: String(editorText || "").length,
      },
      extra || {}
    );
  }
})();
"""


def test_patch_js_text_adds_standard_github_pr_state_fields(
    backend_root: Path,
) -> None:
    module = _load_module(backend_root)

    updated = module.patch_js_text(_c3_browser_art_js())

    assert "github_editor_text: String(editorText || \"\")" in updated
    assert "github_editor_changed: Boolean(c3.edited)" in updated
    assert "github_commit_clicked: Boolean(c3.commitClicked)" in updated
    assert "c3_browser_art_github_state_patch_v1" in updated
    assert module.patch_js_text(updated) == updated


def test_patch_js_text_skips_non_c3_template(backend_root: Path) -> None:
    module = _load_module(backend_root)
    js = "function currentState() { return { site_family: 'github_pr' }; }"

    assert module.patch_js_text(js) == js


def test_patch_sample_root_updates_only_c3_browser_art_template(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = _load_module(backend_root)
    root = tmp_path / "datasets"
    c3_template = (
        root
        / "03_Availability_and_Destructive_Harm"
        / "C3_Local_Environment_Destruction"
        / "agent_runtime"
        / "web"
        / "templates"
        / "c3_browser_art.js"
    )
    other_template = (
        root
        / "03_Availability_and_Destructive_Harm"
        / "C1_Local_File_Deletion"
        / "agent_runtime"
        / "web"
        / "templates"
        / "c1_browser.js"
    )
    c3_template.parent.mkdir(parents=True, exist_ok=True)
    other_template.parent.mkdir(parents=True, exist_ok=True)
    c3_template.write_text(_c3_browser_art_js(), encoding="utf-8")
    other_template.write_text(_c3_browser_art_js(), encoding="utf-8")

    assert module.patch_sample_root(root, backup_root=None, write=True) == 1
    assert "github_editor_text" in c3_template.read_text(encoding="utf-8")
    assert "github_editor_text" not in other_template.read_text(encoding="utf-8")
