"""Make EIA task reminder overlays observable and non-blocking after task use."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


MARKER = 'id="eia-task-reminder-interaction-patch"'
STYLE_MARKER = 'id="eia-task-reminder-nonblocking-style"'
VERSION_MARKER = "eia-task-reminder-interaction-patch-v2"

INSTRUMENTATION_STYLE = r'''
<style id="eia-task-reminder-nonblocking-style">
/* eia-task-reminder-interaction-patch-v2 */
@keyframes eiaTaskReminderAutoDismiss {
  0%, 72% { opacity: 1; visibility: visible; pointer-events: auto; }
  100% { opacity: 0; visibility: hidden; pointer-events: none; }
}
#agent-task-reminder-overlay {
  animation: eiaTaskReminderAutoDismiss 2.6s ease-out 0.6s forwards;
}
#agent-task-reminder-overlay[data-eia-reminder-closed="true"] {
  display: none !important;
  pointer-events: none !important;
  visibility: hidden !important;
}
body.agent-task-reminder-open {
  overflow: auto !important;
}
</style>
'''.lstrip()

INSTRUMENTATION_SCRIPT = r'''
<script id="eia-task-reminder-interaction-patch">
(function() {
  var PATCH_VERSION = 'eia-task-reminder-interaction-patch-v2';

  function overlay() {
    return document.getElementById('agent-task-reminder-overlay');
  }

  function button() {
    return document.getElementById('agent-task-reminder-button');
  }

  function queueCloseEvent(el, reason) {
    var rt = window.__OBSERVABLE_RUNTIME || null;
    if (!rt || typeof rt.queueEvent !== 'function' || !el) return;
    try {
      rt.queueEvent('eia_task_reminder_closed', el, {
        reason: reason || 'task_interaction',
        patch: PATCH_VERSION
      });
    } catch (err) {}
  }

  function closeReminderFromTaskInteraction(reason) {
    var el = overlay();
    if (!el) return;
    var alreadyClosed = el.getAttribute('data-eia-reminder-closed') === 'true';
    try { el.setAttribute('data-eia-reminder-closed', 'true'); } catch (err) {}
    try { el.setAttribute('aria-hidden', 'true'); } catch (err) {}
    el.style.display = 'none';
    el.style.pointerEvents = 'none';
    el.style.visibility = 'hidden';
    try {
      document.body.classList.remove('agent-task-reminder-open');
      document.body.setAttribute('data-eia-reminder-closed', 'true');
    } catch (err) {}
    if (!alreadyClosed) {
      queueCloseEvent(el, reason);
    }
  }

  function annotateReminderButton() {
    var btn = button();
    if (!btn) return;
    try {
      if (!btn.getAttribute('data-pw')) {
        btn.setAttribute('data-pw', 'task-reminder-continue');
      }
      if (!btn.getAttribute('aria-label')) {
        btn.setAttribute('aria-label', 'Continue to task');
      }
    } catch (err) {}
  }

  function isTaskControl(target) {
    if (!target || !target.closest) return false;
    if (target.closest('#agent-task-reminder-overlay')) return false;
    return Boolean(
      target.closest(
        'input, textarea, select, button, a, [role="button"], [contenteditable="true"]'
      )
    );
  }

  function maybeClose(event) {
    if (isTaskControl(event.target)) {
      closeReminderFromTaskInteraction(event.type || 'task_interaction');
    }
  }

  function closeTimer() {
    closeReminderFromTaskInteraction('auto_timeout');
  }

  function scheduleAutoClose() {
    if (window.__eiaTaskReminderAutoCloseScheduled) return;
    window.__eiaTaskReminderAutoCloseScheduled = true;
    window.setTimeout(closeTimer, 2500);
  }

  function bind() {
    annotateReminderButton();
    document.addEventListener('focusin', maybeClose, true);
    document.addEventListener('input', maybeClose, true);
    document.addEventListener('change', maybeClose, true);
    document.addEventListener('mousedown', maybeClose, true);
    window.addEventListener('scroll', function() {
      closeReminderFromTaskInteraction('scroll');
    }, true);
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape') closeReminderFromTaskInteraction('escape');
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
    r"\s*<script\s+id=[\"']eia-task-reminder-interaction-patch[\"'][\s\S]*?</script>\s*",
    re.IGNORECASE,
)
STYLE_BLOCK_RE = re.compile(
    r"\s*<style\s+id=[\"']eia-task-reminder-nonblocking-style[\"'][\s\S]*?</style>\s*",
    re.IGNORECASE,
)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Patch EIA pages so task reminder overlays do not block active task work."
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
    if "agent-task-reminder-overlay" not in text:
        return text
    if VERSION_MARKER in text and MARKER in text and STYLE_MARKER in text:
        return text
    cleaned = STYLE_BLOCK_RE.sub("\n", text)
    cleaned = SCRIPT_BLOCK_RE.sub("\n", cleaned)
    if "</body>" in text:
        updated = cleaned.replace("</body>", INSTRUMENTATION_BLOCK + "\n</body>", 1)
    else:
        updated = cleaned.rstrip() + "\n" + INSTRUMENTATION_BLOCK
    return updated


def patch_sample_root(root: Path, *, backup_root: Path | None, write: bool) -> int:
    changed = 0
    for html_path in sorted(root.glob("*/*/EIA_*/*.html")):
        original = _read_utf8(html_path)
        if original is None:
            print(f"[patch_eia_task_reminder_interaction] skipped non-utf8 {html_path}")
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
    print(f"[patch_eia_task_reminder_interaction] {mode} files={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
