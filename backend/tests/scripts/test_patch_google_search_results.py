from __future__ import annotations

from pathlib import Path

from tests.helpers.scripts import load_module_from_path


def _load_module(backend_root: Path):
    return load_module_from_path(
        "patch_google_search_results_under_test",
        backend_root / "scripts" / "datasets" / "patch_google_search_results.py",
    )


def _google_html() -> str:
    return """
<!doctype html>
<html><body>
<form action="/search" method="get" autocomplete="off">
  <input id="APjFqb" name="q" type="text" aria-label="Search">
  <input type="submit" name="btnK" value="Google Search">
  <input type="submit" name="btnI" value="I'm Feeling Lucky">
</form>
<script src="../../agent_runtime/web/bootstrap.js"></script>
</body></html>
"""


def test_patch_html_text_adds_search_result_state(backend_root: Path) -> None:
    module = _load_module(backend_root)

    updated = module.patch_html_text(_google_html())

    assert "asp-google-search-results-patch-v3" in updated
    assert 'id="asp-google-search-results-patch"' in updated
    assert 'id="asp-google-search-results-style"' in updated
    assert "event.preventDefault()" in updated
    assert "addEventListener('click'" in updated
    assert "addEventListener('submit'" in updated
    assert "google_search_results_rendered" in updated
    assert "flushEvents(true)" in updated
    assert "handleSearch(input)" in updated
    assert "asp-google-search-results" in updated
    assert "history.replaceState" in updated
    assert "search-results" in updated
    assert "search-submit" in updated
    assert module.patch_html_text(updated) == updated


def test_patch_html_text_upgrades_existing_v1_patch(backend_root: Path) -> None:
    module = _load_module(backend_root)
    html = _google_html().replace(
        "</body>",
        """
<style id="asp-google-search-results-style">
/* asp-google-search-results-patch-v1 */
</style>
<script id="asp-google-search-results-patch">
(function() {
  var PATCH_VERSION = 'asp-google-search-results-patch-v1';
})();
</script>
</body>
""",
    )

    updated = module.patch_html_text(html)

    assert "asp-google-search-results-patch-v3" in updated
    assert "asp-google-search-results-patch-v1" not in updated
    assert updated.count('id="asp-google-search-results-patch"') == 1


def test_patch_html_text_upgrades_existing_v2_patch(backend_root: Path) -> None:
    module = _load_module(backend_root)
    html = _google_html().replace(
        "</body>",
        """
<style id="asp-google-search-results-style">
/* asp-google-search-results-patch-v2 */
</style>
<script id="asp-google-search-results-patch">
(function() {
  var PATCH_VERSION = 'asp-google-search-results-patch-v2';
})();
</script>
</body>
""",
    )

    updated = module.patch_html_text(html)

    assert "asp-google-search-results-patch-v3" in updated
    assert "asp-google-search-results-patch-v2" not in updated
    assert updated.count('id="asp-google-search-results-patch"') == 1


def test_patch_html_text_skips_non_google_page(backend_root: Path) -> None:
    module = _load_module(backend_root)
    html = "<html><body><form><input name='q'></form></body></html>"

    assert module.patch_html_text(html) == html


def test_patch_sample_root_limits_to_g1_and_g3_by_default(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = _load_module(backend_root)
    root = tmp_path / "datasets"
    g1_page = (
        root
        / "07_Harmful_Search_and_Reconnaissance"
        / "G1_Harmful_Search_Assistance"
        / "Browser-art_G1_1"
        / "google"
        / "index.html"
    )
    g2_page = (
        root
        / "07_Harmful_Search_and_Reconnaissance"
        / "G2_Cyberstalking_and_Private_Record_Collection"
        / "Browser-art_G2_1"
        / "google"
        / "index.html"
    )
    g3_page = (
        root
        / "07_Harmful_Search_and_Reconnaissance"
        / "G3_Copyright_and_Illegal_Content_Access"
        / "Browser-art_G3_1"
        / "google"
        / "index.html"
    )
    for path in (g1_page, g2_page, g3_page):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_google_html(), encoding="utf-8")

    assert (
        module.patch_sample_root(
            root,
            sample_id_prefixes=["Browser-art_G1_", "Browser-art_G3_"],
            backup_root=None,
            write=True,
        )
        == 2
    )
    assert "asp-google-search-results-patch" in g1_page.read_text(encoding="utf-8")
    assert "asp-google-search-results-patch" not in g2_page.read_text(
        encoding="utf-8"
    )
    assert "asp-google-search-results-patch" in g3_page.read_text(encoding="utf-8")
    assert (
        module.patch_sample_root(
            root,
            sample_id_prefixes=["Browser-art_G1_", "Browser-art_G3_"],
            backup_root=None,
            write=True,
        )
        == 0
    )
