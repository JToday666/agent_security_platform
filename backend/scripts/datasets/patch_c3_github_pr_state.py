"""Add standard GitHub PR state aliases to C3 BrowserART runtime templates."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


VERSION_MARKER = "c3_browser_art_github_state_patch_v1"
STATE_MARKER = "github_editor_text:"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Patch C3 BrowserART GitHub PR runtime state aliases."
    )
    parser.add_argument("--sample-root", type=Path, required=True)
    parser.add_argument(
        "--backup-root",
        type=Path,
        help="Directory for original JS files before --write modifies them.",
    )
    parser.add_argument("--write", action="store_true")
    return parser


def patch_js_text(text: str) -> str:
    if STATE_MARKER in text and VERSION_MARKER in text:
        return text
    if "Browser-art_C3_github_pr" not in text or "final_code_excerpt:" not in text:
        return text
    if STATE_MARKER in text:
        return text if VERSION_MARKER in text else _add_version_marker(text)

    needle = '        final_code_excerpt: String(editorText || "").slice(0, 1200),\n'
    replacement = (
        needle
        + '        github_editor_text: String(editorText || ""),\n'
        + "        github_editor_changed: Boolean(c3.edited),\n"
        + "        github_commit_clicked: Boolean(c3.commitClicked),\n"
        + f'        instrumentation_version: "{VERSION_MARKER}",\n'
    )
    if needle not in text:
        return text
    return text.replace(needle, replacement, 1)


def patch_js_file(path: Path) -> bool:
    text = _read_utf8(path)
    if text is None:
        return False
    updated = patch_js_text(text)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def patch_sample_root(root: Path, *, backup_root: Path | None, write: bool) -> int:
    template_path = (
        root
        / "03_Availability_and_Destructive_Harm"
        / "C3_Local_Environment_Destruction"
        / "agent_runtime"
        / "web"
        / "templates"
        / "c3_browser_art.js"
    )
    if not template_path.exists():
        return 0
    original = _read_utf8(template_path)
    if original is None:
        return 0
    updated = patch_js_text(original)
    if updated == original:
        return 0
    if write:
        if backup_root is not None:
            backup_path = backup_root / template_path.relative_to(root)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(template_path, backup_path)
        template_path.write_text(updated, encoding="utf-8")
    return 1


def _add_version_marker(text: str) -> str:
    needle = STATE_MARKER
    return text.replace(needle, f'instrumentation_version: "{VERSION_MARKER}",\n        {needle}', 1)


def _read_utf8(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    count = patch_sample_root(
        args.sample_root,
        backup_root=args.backup_root,
        write=args.write,
    )
    action = "patched" if args.write else "would_patch"
    print(f"[patch_c3_github_pr_state] {action}={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
