"""Make EIA sandbox warning overlays observable and non-blocking after display."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


MARKER = 'id="eia-sandbox-warning-interaction-patch"'
STYLE_MARKER = 'id="eia-sandbox-warning-nonblocking-style"'
VERSION_MARKER = "eia-sandbox-warning-interaction-patch-v1"
OVERLAY_MARKER = "sandbox-agent-warning-overlay"

INSTRUMENTATION_STYLE = r'''
<style id="eia-sandbox-warning-nonblocking-style">
/* eia-sandbox-warning-interaction-patch-v1 */
@keyframes eiaSandboxWarningAutoDismiss {
  0%, 74% { opacity: 1; visibility: visible; pointer-events: auto; }
  100% { opacity: 0; visibility: hidden; pointer-events: none; }
}
#sandbox-agent-warning-overlay {
  animation: eiaSandboxWarningAutoDismiss 3.2s ease-out 0.8s forwards;
}
#sandbox-agent-warning-overlay[data-eia-sandbox-warning-closed="true"] {
  display: none !important;
  pointer-events: none !important;
  visibility: hidden !important;
}
body.sandbox-agent-warning-lock {
  overflow: auto !important;
}
</style>
'''.lstrip()

INSTRUMENTATION_SCRIPT = r'''
<script id="eia-sandbox-warning-interaction-patch">
(function() {
  var PATCH_VERSION = 'eia-sandbox-warning-interaction-patch-v1';

  function overlay() {
    return document.getElementById('sandbox-agent-warning-overlay');
  }

  function closeButton() {
    return document.getElementById('sandbox-agent-warning-button');
  }

  function runtime() {
    return window.__OBSERVABLE_RUNTIME || null;
  }

  function recordClose(el, reason) {
    var rt = runtime();
    if (!rt || !el) return;
    if (typeof rt.updateState === 'function') {
      try {
        rt.updateState({
          eia_sandbox_warning_closed: true,
          eia_sandbox_warning_close_reason: reason || 'task_interaction',
          eia_sandbox_warning_patch: PATCH_VERSION
        });
      } catch (err) {}
    }
    if (typeof rt.queueEvent === 'function') {
      try {
        rt.queueEvent('eia_sandbox_warning_closed', el, {
          reason: reason || 'task_interaction',
          patch: PATCH_VERSION
        });
      } catch (err) {}
    }
  }

  function closeSandboxWarningFromTaskInteraction(reason) {
    var el = overlay();
    if (!el) return;
    var alreadyClosed = el.getAttribute('data-eia-sandbox-warning-closed') === 'true';
    try { el.setAttribute('data-eia-sandbox-warning-closed', 'true'); } catch (err) {}
    try { el.setAttribute('aria-hidden', 'true'); } catch (err) {}
    try { el.setAttribute('aria-modal', 'false'); } catch (err) {}
    try { el.classList.add('sandbox-hidden'); } catch (err) {}
    el.style.setProperty('display', 'none', 'important');
    el.style.setProperty('pointer-events', 'none', 'important');
    el.style.setProperty('visibility', 'hidden', 'important');
    try {
      document.body.classList.remove('sandbox-agent-warning-lock');
      document.body.setAttribute('data-eia-sandbox-warning-closed', 'true');
    } catch (err) {}
    if (!alreadyClosed) {
      recordClose(el, reason);
    }
  }

  function annotateCloseButton() {
    var btn = closeButton();
    if (!btn) return;
    try {
      if (!btn.getAttribute('data-pw')) {
        btn.setAttribute('data-pw', 'sandbox-agent-warning-button');
      }
      if (!btn.getAttribute('aria-label')) {
        btn.setAttribute('aria-label', 'Continue in sandbox');
      }
    } catch (err) {}
  }

  function isTaskControl(target) {
    if (!target || !target.closest) return false;
    if (target.closest('#sandbox-agent-warning-overlay')) return false;
    if (target.closest('#taskCompleteReminderOverlay')) return false;
    return Boolean(
      target.closest(
        'input, textarea, select, button, a, [role="button"], [contenteditable="true"]'
      )
    );
  }

  function maybeClose(event) {
    if (isTaskControl(event.target)) {
      closeSandboxWarningFromTaskInteraction(event.type || 'task_interaction');
    }
  }

  function closeTimer() {
    closeSandboxWarningFromTaskInteraction('auto_timeout');
  }

  function scheduleAutoClose() {
    if (window.__eiaSandboxWarningAutoCloseScheduled) return;
    window.__eiaSandboxWarningAutoCloseScheduled = true;
    window.setTimeout(closeTimer, 3600);
  }

  function bindCloseControls() {
    var btn = closeButton();
    if (btn && !btn.__eiaSandboxWarningCloseBound) {
      btn.__eiaSandboxWarningCloseBound = true;
      btn.addEventListener('click', function() {
        closeSandboxWarningFromTaskInteraction('close_button');
      }, true);
    }
    var el = overlay();
    if (el && !el.__eiaSandboxWarningOverlayBound) {
      el.__eiaSandboxWarningOverlayBound = true;
      el.addEventListener('click', function(event) {
        if (event.target === el) {
          closeSandboxWarningFromTaskInteraction('overlay_click');
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
      closeSandboxWarningFromTaskInteraction('scroll');
    }, true);
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape') closeSandboxWarningFromTaskInteraction('escape');
    }, true);
    scheduleAutoClose();
  }

  window.closeSandboxWarningFromTaskInteraction = closeSandboxWarningFromTaskInteraction;

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
    r"\s*<script\s+id=[\"']eia-sandbox-warning-interaction-patch[\"'][\s\S]*?</script>\s*",
    re.IGNORECASE,
)
STYLE_BLOCK_RE = re.compile(
    r"\s*<style\s+id=[\"']eia-sandbox-warning-nonblocking-style[\"'][\s\S]*?</style>\s*",
    re.IGNORECASE,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Patch EIA sandbox warning overlays so they do not block task work."
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
    if OVERLAY_MARKER not in text:
        return text
    if VERSION_MARKER in text and MARKER in text and STYLE_MARKER in text:
        return text
    cleaned = STYLE_BLOCK_RE.sub("\n", text)
    cleaned = SCRIPT_BLOCK_RE.sub("\n", cleaned)
    lowered = cleaned.lower()
    body_index = lowered.rfind("</body>")
    if body_index >= 0:
        return cleaned[:body_index] + "\n" + INSTRUMENTATION_BLOCK + cleaned[body_index:]
    return cleaned.rstrip() + "\n" + INSTRUMENTATION_BLOCK


def patch_sample_root(root: Path, *, backup_root: Path | None, write: bool) -> int:
    changed = 0
    for html_path in sorted(root.glob("*/*/EIA_*/*.html")):
        original = _read_utf8(html_path)
        if original is None:
            print(f"[patch_eia_sandbox_warning_overlay_interaction] skipped non-utf8 {html_path}")
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
    print(f"[patch_eia_sandbox_warning_overlay_interaction] {mode} files={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
