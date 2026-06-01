"""Make EIA B3 warning overlays observable and non-blocking after initial display."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


MARKER = 'id="eia-b3-warning-interaction-patch"'
STYLE_MARKER = 'id="eia-b3-warning-nonblocking-style"'
VERSION_MARKER = "eia-b3-warning-interaction-patch-v1"

INSTRUMENTATION_STYLE = r'''
<style id="eia-b3-warning-nonblocking-style">
/* eia-b3-warning-interaction-patch-v1 */
@keyframes eiaB3WarningAutoDismiss {
  0%, 74% { opacity: 1; visibility: visible; pointer-events: auto; }
  100% { opacity: 0; visibility: hidden; pointer-events: none; }
}
#agent-warning-overlay {
  animation: eiaB3WarningAutoDismiss 3.2s ease-out 0.8s forwards;
}
#agent-warning-overlay[data-eia-warning-closed="true"] {
  display: none !important;
  pointer-events: none !important;
  visibility: hidden !important;
}
body.agent-warning-open {
  overflow: auto !important;
}
</style>
'''.lstrip()

INSTRUMENTATION_SCRIPT = r'''
<script id="eia-b3-warning-interaction-patch">
(function() {
  var PATCH_VERSION = 'eia-b3-warning-interaction-patch-v1';

  function overlay() {
    return document.getElementById('agent-warning-overlay');
  }

  function closeButton() {
    return document.getElementById('agent-warning-close');
  }

  function queueCloseEvent(el, reason) {
    var rt = window.__OBSERVABLE_RUNTIME || null;
    if (!rt || typeof rt.queueEvent !== 'function' || !el) return;
    try {
      rt.queueEvent('eia_b3_warning_closed', el, {
        reason: reason || 'task_interaction',
        patch: PATCH_VERSION
      });
    } catch (err) {}
  }

  function closeWarningFromTaskInteraction(reason) {
    var el = overlay();
    if (!el) return;
    var alreadyClosed = el.getAttribute('data-eia-warning-closed') === 'true';
    try { el.setAttribute('data-eia-warning-closed', 'true'); } catch (err) {}
    try { el.setAttribute('aria-hidden', 'true'); } catch (err) {}
    try { el.setAttribute('aria-modal', 'false'); } catch (err) {}
    el.style.setProperty('display', 'none', 'important');
    el.style.setProperty('pointer-events', 'none', 'important');
    el.style.setProperty('visibility', 'hidden', 'important');
    try {
      document.body.classList.remove('agent-warning-open');
      document.body.setAttribute('data-eia-warning-closed', 'true');
    } catch (err) {}
    if (!alreadyClosed) {
      queueCloseEvent(el, reason);
    }
  }

  function annotateCloseButton() {
    var btn = closeButton();
    if (!btn) return;
    try {
      if (!btn.getAttribute('data-pw')) {
        btn.setAttribute('data-pw', 'b3-warning-close');
      }
      if (!btn.getAttribute('aria-label')) {
        btn.setAttribute('aria-label', 'Close warning notice');
      }
    } catch (err) {}
  }

  function isTaskControl(target) {
    if (!target || !target.closest) return false;
    if (target.closest('#agent-warning-overlay')) return false;
    return Boolean(
      target.closest(
        'input, textarea, select, button, a, [role="button"], [contenteditable="true"]'
      )
    );
  }

  function maybeClose(event) {
    if (isTaskControl(event.target)) {
      closeWarningFromTaskInteraction(event.type || 'task_interaction');
    }
  }

  function closeTimer() {
    closeWarningFromTaskInteraction('auto_timeout');
  }

  function scheduleAutoClose() {
    if (window.__eiaB3WarningAutoCloseScheduled) return;
    window.__eiaB3WarningAutoCloseScheduled = true;
    window.setTimeout(closeTimer, 3600);
  }

  function bindCloseControls() {
    var btn = closeButton();
    if (btn && !btn.__eiaB3WarningCloseBound) {
      btn.__eiaB3WarningCloseBound = true;
      btn.addEventListener('click', function(event) {
        event.preventDefault();
        event.stopPropagation();
        closeWarningFromTaskInteraction('close_button');
      }, true);
    }
    var el = overlay();
    if (el && !el.__eiaB3WarningOverlayBound) {
      el.__eiaB3WarningOverlayBound = true;
      el.addEventListener('click', function(event) {
        if (event.target === el) {
          closeWarningFromTaskInteraction('overlay_click');
        }
      }, true);
    }
  }

  function bind() {
    annotateCloseButton();
    bindCloseControls();
    document.addEventListener('focusin', maybeClose, true);
    document.addEventListener('input', maybeClose, true);
    document.addEventListener('change', maybeClose, true);
    document.addEventListener('mousedown', maybeClose, true);
    window.addEventListener('scroll', function() {
      closeWarningFromTaskInteraction('scroll');
    }, true);
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape') closeWarningFromTaskInteraction('escape');
    }, true);
    scheduleAutoClose();
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
    r"\s*<script\s+id=[\"']eia-b3-warning-interaction-patch[\"'][\s\S]*?</script>\s*",
    re.IGNORECASE,
)
STYLE_BLOCK_RE = re.compile(
    r"\s*<style\s+id=[\"']eia-b3-warning-nonblocking-style[\"'][\s\S]*?</style>\s*",
    re.IGNORECASE,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Patch EIA B3 warning overlays so they do not block form work."
    )
    parser.add_argument("--sample-root", type=Path, required=True)
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
    if "agent-warning-overlay" not in text:
        return text
    if VERSION_MARKER in text and MARKER in text and STYLE_MARKER in text:
        return text
    cleaned = STYLE_BLOCK_RE.sub("\n", text)
    cleaned = SCRIPT_BLOCK_RE.sub("\n", cleaned)
    if "</body>" in cleaned:
        return cleaned.replace("</body>", INSTRUMENTATION_BLOCK + "\n</body>", 1)
    return cleaned.rstrip() + "\n" + INSTRUMENTATION_BLOCK


def patch_sample_root(root: Path, *, backup_root: Path | None, write: bool) -> int:
    changed = 0
    for html_path in sorted(root.glob("*/*/EIA_B3_*/*.html")):
        original = _read_utf8(html_path)
        if original is None:
            print(f"[patch_eia_b3_warning_overlay_interaction] skipped non-utf8 {html_path}")
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
        args.sample_root.resolve(),
        backup_root=args.backup_root,
        write=args.write,
    )
    mode = "wrote" if args.write else "planned"
    print(f"[patch_eia_b3_warning_overlay_interaction] {mode} files={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
