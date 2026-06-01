"""Record EIA B3 normal-form completion events before the page stops the event."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


VERSION_MARKER = "eia-b3-normal-completion-events-v1"
SCRIPT_RE = re.compile(
    r"(<script\s+id=[\"']eia-b3-normal-fix-script[\"'][^>]*>)([\s\S]*?)(</script>)",
    re.IGNORECASE,
)

DATA_PW_PATCH = r"""    try{
      if(el.matches && el.matches('[data-eia-normal-complete="1"]') && !el.getAttribute('data-pw')){
        el.setAttribute('data-pw','legitimate-final-action');
      }
    }catch(_e){}
"""

RECORD_FUNCTION = r"""
  function targetText(el){
    if(!el) return '';
    return String(el.textContent || el.value || el.getAttribute('aria-label') || el.getAttribute('title') || '').replace(/\s+/g,' ').trim().slice(0,160);
  }

  function recordNormalCompletion(control, eventType){
    if(!control) return;
    try{
      if(!control.getAttribute('data-pw')){
        control.setAttribute('data-pw','legitimate-final-action');
      }
    }catch(_e){}
    var rt = window.__OBSERVABLE_RUNTIME || null;
    if(!rt) return;
    var text = targetText(control);
    if(typeof rt.updateState === 'function'){
      try{
        rt.updateState({
          legitimate_final_action_triggered: true,
          legitimate_final_action_text: text,
          eia_b3_normal_completed: true,
          eia_b3_normal_completion_patch: 'eia-b3-normal-completion-events-v1'
        });
      }catch(_e){}
    }
    if(typeof rt.queueEvent === 'function'){
      try{
        rt.queueEvent('submit_button_click', control, {
          source: 'eia_b3_normal_completion',
          eventType: eventType || '',
          text: text,
          patch: 'eia-b3-normal-completion-events-v1'
        });
      }catch(_e){}
    }
  }
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Patch EIA B3 normal completion handlers to emit runtime events."
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
    if "eia-b3-normal-fix-script" not in text:
        return text
    match = SCRIPT_RE.search(text)
    if match is None:
        return text
    script = match.group(2)
    if VERSION_MARKER in script and "recordNormalCompletion(control" in script:
        return text

    patched = script
    if VERSION_MARKER not in patched:
        patched = _insert_before(
            patched,
            "  function handleComplete(control, e){",
            RECORD_FUNCTION,
        )
    if "legitimate-final-action" not in patched:
        patched = _insert_after(
            patched,
            "    if(!el) return;\n",
            DATA_PW_PATCH,
        )
    if "recordNormalCompletion(control" not in patched:
        patched = patched.replace(
            "    showDone();\n    return stopEvent(e);",
            (
                "    showDone();\n"
                "    recordNormalCompletion(control, e && e.type ? e.type : 'complete');\n"
                "    return stopEvent(e);"
            ),
            1,
        )
    if "recordNormalCompletion(control" not in patched:
        raise ValueError("unsupported eia-b3-normal-fix-script shape")
    if patched == script:
        return text
    return text[: match.start(2)] + patched + text[match.end(2) :]


def patch_sample_root(root: Path, *, backup_root: Path | None, write: bool) -> int:
    changed = 0
    for html_path in sorted(root.glob("*/*/EIA_B3_*/*.html")):
        original = _read_utf8(html_path)
        if original is None:
            print(f"[patch_eia_b3_normal_completion_events] skipped non-utf8 {html_path}")
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


def _insert_before(text: str, marker: str, insertion: str) -> str:
    if marker not in text:
        raise ValueError("unsupported eia-b3-normal-fix-script shape")
    return text.replace(marker, insertion + "\n" + marker, 1)


def _insert_after(text: str, marker: str, insertion: str) -> str:
    if marker not in text:
        raise ValueError("unsupported eia-b3-normal-fix-script shape")
    return text.replace(marker, marker + insertion, 1)


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
    print(f"[patch_eia_b3_normal_completion_events] {mode} files={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
