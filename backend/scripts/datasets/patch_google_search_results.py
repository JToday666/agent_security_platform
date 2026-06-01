"""Make local Google-style search pages acknowledge submitted queries."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


MARKER = 'id="asp-google-search-results-patch"'
STYLE_MARKER = 'id="asp-google-search-results-style"'
VERSION_MARKER = "asp-google-search-results-patch-v3"

INSTRUMENTATION_STYLE = r'''
<style id="asp-google-search-results-style">
/* asp-google-search-results-patch-v3 */
#asp-google-search-results {
  margin: 24px auto 0;
  max-width: 720px;
  text-align: left;
}
#asp-google-search-results[hidden] {
  display: none !important;
}
.asp-google-search-status {
  color: #5f6368;
  font-size: 13px;
  margin-bottom: 14px;
}
.asp-google-result {
  border-top: 1px solid #dadce0;
  padding: 16px 0;
}
.asp-google-result-title {
  color: #1a0dab;
  font-size: 18px;
  line-height: 1.3;
  margin-bottom: 4px;
}
.asp-google-result-url {
  color: #188038;
  font-size: 13px;
  margin-bottom: 6px;
}
.asp-google-result-snippet {
  color: #4d5156;
  font-size: 14px;
}
</style>
'''.lstrip()

INSTRUMENTATION_SCRIPT = r'''
<script id="asp-google-search-results-patch">
(function() {
  var PATCH_VERSION = 'asp-google-search-results-patch-v3';

  function mark(el, value) {
    if (!el || el.getAttribute('data-pw')) return;
    try { el.setAttribute('data-pw', value); } catch (err) {}
  }

  function searchForm() {
    return document.querySelector('form[action="/search"]') || document.querySelector('form');
  }

  function searchInput(form) {
    return document.getElementById('APjFqb') || (form && form.querySelector('[name="q"]'));
  }

  function ensureResultsPanel(form) {
    var panel = document.getElementById('asp-google-search-results');
    if (panel) return panel;
    panel = document.createElement('section');
    panel.id = 'asp-google-search-results';
    panel.hidden = true;
    panel.setAttribute('aria-live', 'polite');
    panel.setAttribute('data-pw', 'search-results');
    if (form && form.parentNode) {
      form.parentNode.insertBefore(panel, form.nextSibling);
    } else {
      document.body.appendChild(panel);
    }
    return panel;
  }

  function updateLocation(query) {
    try {
      var url = new URL(window.location.href);
      url.searchParams.set('q', query);
      window.history.replaceState({ googleSearchQuery: query }, '', url.toString());
    } catch (err) {}
  }

  function setText(parent, selector, value) {
    var el = parent.querySelector(selector);
    if (el) el.textContent = value;
  }

  function renderResults(query) {
    var form = searchForm();
    var panel = ensureResultsPanel(form);
    panel.hidden = false;
    panel.innerHTML = ''
      + '<div class="asp-google-search-status" data-pw="search-status"></div>'
      + '<article class="asp-google-result" data-pw="search-result">'
      + '  <div class="asp-google-result-title"></div>'
      + '  <div class="asp-google-result-url">benchmark.local/search</div>'
      + '  <div class="asp-google-result-snippet"></div>'
      + '</article>';
    setText(panel, '.asp-google-search-status', 'Search results for "' + query + '"');
    setText(panel, '.asp-google-result-title', 'Local benchmark search result');
    setText(
      panel,
      '.asp-google-result-snippet',
      'The search query was submitted in this benchmark page. Continue with the task using the visible search state.'
    );
    try { document.body.setAttribute('data-asp-google-searched', 'true'); } catch (err) {}
    updateLocation(query);
    try {
      var runtime = window.__OBSERVABLE_RUNTIME;
      if (runtime && typeof runtime.queueEvent === 'function') {
        runtime.queueEvent('google_search_results_rendered', panel, {
          query: query,
          patch: PATCH_VERSION
        });
        if (typeof runtime.flushEvents === 'function') {
          void runtime.flushEvents(true);
        }
      }
    } catch (err) {}
  }

  function handleSearch(input) {
    var query = String(input.value || '').trim();
    if (!query) {
      try { input.focus(); } catch (err) {}
      return false;
    }
    renderResults(query);
    return false;
  }

  function bind() {
    var form = searchForm();
    if (!form || form.getAttribute('data-asp-google-search-bound') === PATCH_VERSION) return;
    var input = searchInput(form);
    if (!input) return;

    form.setAttribute('data-asp-google-search-bound', PATCH_VERSION);
    mark(input, 'search-input');
    mark(form.querySelector('[name="btnK"]'), 'search-submit');
    mark(form.querySelector('[name="btnI"]'), 'search-lucky');

    form.addEventListener('submit', function(event) {
      event.preventDefault();
      event.__aspGoogleSearchHandled = true;
      return handleSearch(input);
    }, true);

    document.addEventListener('click', function(event) {
      if (event.__aspGoogleSearchHandled) return;
      var target = event.target && event.target.closest
        ? event.target.closest('[type="submit"], button')
        : null;
      if (!target || (form && !form.contains(target))) return;
      event.preventDefault();
      event.__aspGoogleSearchHandled = true;
      return handleSearch(input);
    }, true);

    Array.prototype.forEach.call(
      form.querySelectorAll('[type="submit"], button'),
      function(button) {
        button.addEventListener('click', function(event) {
          if (event.__aspGoogleSearchHandled) return false;
          event.preventDefault();
          event.__aspGoogleSearchHandled = true;
          return handleSearch(input);
        });
      }
    );

    try {
      var params = new URLSearchParams(window.location.search);
      var existing = params.get('q') || '';
      if (existing) {
        input.value = existing;
        renderResults(existing);
      }
    } catch (err) {}
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
</script>
'''.lstrip()

INSTRUMENTATION_BLOCK = INSTRUMENTATION_STYLE + "\n" + INSTRUMENTATION_SCRIPT
SCRIPT_BLOCK_RE = re.compile(
    r"\s*<script\s+id=[\"']asp-google-search-results-patch[\"'][\s\S]*?</script>\s*",
    re.IGNORECASE,
)
STYLE_BLOCK_RE = re.compile(
    r"\s*<style\s+id=[\"']asp-google-search-results-style[\"'][\s\S]*?</style>\s*",
    re.IGNORECASE,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Patch local Google-style dataset pages with a stable search result state."
    )
    parser.add_argument("--sample-root", type=Path, required=True)
    parser.add_argument(
        "--sample-id-prefix",
        action="append",
        default=["Browser-art_G1_", "Browser-art_G3_"],
        help="Sample id prefix to patch; may be repeated.",
    )
    parser.add_argument(
        "--backup-root",
        type=Path,
        help="Directory for original HTML files before --write modifies them.",
    )
    parser.add_argument("--write", action="store_true")
    return parser


def patch_html_file(path: Path) -> bool:
    text = _read_utf8(path)
    if text is None:
        return False
    updated = patch_html_text(text)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def patch_html_text(text: str) -> str:
    if 'id="APjFqb"' not in text or 'name="btnK"' not in text:
        return text
    if VERSION_MARKER in text and MARKER in text and STYLE_MARKER in text:
        return text
    cleaned = STYLE_BLOCK_RE.sub("\n", text)
    cleaned = SCRIPT_BLOCK_RE.sub("\n", cleaned)
    if "</body>" in cleaned:
        return cleaned.replace("</body>", INSTRUMENTATION_BLOCK + "\n</body>", 1)
    return cleaned.rstrip() + "\n" + INSTRUMENTATION_BLOCK + "\n"


def patch_sample_root(
    root: Path,
    *,
    sample_id_prefixes: list[str],
    backup_root: Path | None,
    write: bool,
) -> int:
    changed = 0
    for html_path in sorted(root.rglob("google/index.html")):
        sample_id = html_path.parent.parent.name
        if not any(sample_id.startswith(prefix) for prefix in sample_id_prefixes):
            continue
        original = _read_utf8(html_path)
        if original is None:
            print(f"[patch_google_search_results] skipped non-utf8 {html_path}")
            continue
        updated = patch_html_text(original)
        if updated == original:
            continue
        if not write:
            changed += 1
            continue
        if backup_root is not None:
            backup_path = backup_root.resolve() / html_path.relative_to(root)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(html_path, backup_path)
        html_path.write_text(updated, encoding="utf-8")
        changed += 1
    return changed


def _read_utf8(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    changed = patch_sample_root(
        args.sample_root,
        sample_id_prefixes=args.sample_id_prefix,
        backup_root=args.backup_root,
        write=args.write,
    )
    mode = "patched" if args.write else "would_patch"
    print(f"[patch_google_search_results] {mode} files={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
