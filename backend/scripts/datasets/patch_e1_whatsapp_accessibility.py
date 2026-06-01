"""Add non-invasive accessibility hooks to E1 WhatsApp benchmark pages."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


MARKER = 'id="e1-whatsapp-accessibility-patch"'
VERSION_MARKER = "e1-whatsapp-accessibility-patch-v2"
OLD_BLOCK_START = '<script id="e1-whatsapp-accessibility-patch">'

INSTRUMENTATION_SCRIPT = r'''
<script id="e1-whatsapp-accessibility-patch">
(function() {
  var PATCH_VERSION = 'e1-whatsapp-accessibility-patch-v2';

  function slug(value) {
    return String(value || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'unknown';
  }

  function setAttr(el, name, value, overwrite) {
    if (!el || !el.setAttribute || (!overwrite && el.getAttribute(name))) return;
    try { el.setAttribute(name, value); } catch (err) {}
  }

  function contactName(item) {
    if (!item) return '';
    var name = item.querySelector ? item.querySelector('.name') : null;
    return String(
      (name && name.textContent) ||
      item.getAttribute('data-contact-name') ||
      item.textContent ||
      ''
    ).replace(/\s+/g, ' ').trim();
  }

  function runtime() {
    return window.__OBSERVABLE_RUNTIME || null;
  }

  function patchControls() {
    var searchInput = document.getElementById('searchInput');
    var messageInput = document.getElementById('messageInput');
    var sendButton = document.getElementById('sendButton');
    setAttr(searchInput, 'aria-label', 'Search WhatsApp contacts', true);
    setAttr(searchInput, 'title', 'Search WhatsApp contacts', false);
    setAttr(messageInput, 'aria-label', 'Type WhatsApp message', true);
    setAttr(messageInput, 'title', 'Type WhatsApp message', false);
    setAttr(sendButton, 'aria-label', 'Send WhatsApp message', true);
    setAttr(sendButton, 'title', 'Send WhatsApp message', false);
  }

  function patchContact(item) {
    var name = contactName(item);
    if (!name) return;
    setAttr(item, 'role', 'button', true);
    setAttr(item, 'tabindex', '0', false);
    setAttr(item, 'data-contact-name', name, true);
    setAttr(item, 'data-pw', 'chat-contact-' + slug(name), false);
    setAttr(item, 'aria-label', 'Open chat with ' + name, true);
    setAttr(item, 'title', 'Open chat with ' + name, false);
  }

  function patchContacts() {
    var list = document.getElementById('userList');
    if (!list || !list.querySelectorAll) return;
    Array.prototype.forEach.call(list.querySelectorAll('li'), patchContact);
  }

  function selectedContactFromEvent(event) {
    var target = event && event.target;
    if (!target || !target.closest) return null;
    return target.closest('#userList li');
  }

  function recordSelection(item) {
    var rt = runtime();
    var name = contactName(item);
    if (!rt || !name) return;
    if (typeof rt.updateState === 'function') {
      rt.updateState({ whatsapp_selected_chat: name });
    }
    if (typeof rt.queueEvent === 'function') {
      rt.queueEvent('whatsapp_chat_selected', item, { active_chat: name });
    }
  }

  function bindList() {
    var list = document.getElementById('userList');
    if (!list || list.__aspE1WhatsappAccessibilityBound) return;
    list.__aspE1WhatsappAccessibilityBound = PATCH_VERSION;
    list.addEventListener('click', function(event) {
      var item = selectedContactFromEvent(event);
      if (!item) return;
      patchContact(item);
      window.setTimeout(function() {
        recordSelection(item);
      }, 0);
    }, false);
    list.addEventListener('keydown', function(event) {
      var item = selectedContactFromEvent(event);
      if (!item || (event.key !== 'Enter' && event.key !== ' ')) return;
      event.preventDefault();
      item.click();
    }, true);
  }

  function bind() {
    patchControls();
    patchContacts();
    bindList();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
  window.setTimeout(bind, 0);
  window.setTimeout(bind, 500);
  try {
    new MutationObserver(bind).observe(document.documentElement, {
      childList: true,
      subtree: true
    });
  } catch (err) {}
})();
</script>
'''.lstrip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Patch E1 WhatsApp pages with stable contact/input/send semantics."
    )
    parser.add_argument("--sample-root", type=Path, required=True)
    parser.add_argument(
        "--sample-id-prefix",
        action="append",
        default=["Browser-art_E1_"],
        help="Sample id prefix to patch; may be repeated.",
    )
    parser.add_argument(
        "--backup-root",
        type=Path,
        help="Directory for original HTML files before --write modifies them.",
    )
    parser.add_argument("--write", action="store_true")
    return parser


def patch_html_text(text: str) -> str:
    if MARKER in text and VERSION_MARKER in text:
        return text
    if not _looks_like_whatsapp_page(text):
        return text
    text = _remove_existing_patch(text)
    if "</body>" in text:
        return text.replace("</body>", INSTRUMENTATION_SCRIPT + "\n</body>", 1)
    return text.rstrip() + "\n" + INSTRUMENTATION_SCRIPT


def patch_html_file(path: Path) -> bool:
    text = _read_utf8(path)
    if text is None:
        return False
    updated = patch_html_text(text)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def patch_sample_root(
    root: Path,
    *,
    sample_id_prefixes: list[str],
    backup_root: Path | None,
    write: bool,
) -> int:
    changed = 0
    for sample_dir in sorted(root.rglob("Browser-art_*")):
        if not sample_dir.is_dir():
            continue
        if not any(sample_dir.name.startswith(prefix) for prefix in sample_id_prefixes):
            continue
        html_path = sample_dir / "whatsapp" / "index.html"
        if not html_path.exists():
            continue
        original = _read_utf8(html_path)
        if original is None:
            continue
        updated = patch_html_text(original)
        if updated == original:
            continue
        changed += 1
        if write:
            if backup_root is not None:
                backup_path = backup_root / html_path.relative_to(root)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(html_path, backup_path)
            html_path.write_text(updated, encoding="utf-8")
    return changed


def _looks_like_whatsapp_page(text: str) -> bool:
    required = (
        'id="userList"',
        'id="messageInput"',
        'id="sendButton"',
        "function loadUsers()",
    )
    return all(marker in text for marker in required)


def _remove_existing_patch(text: str) -> str:
    start = text.find(OLD_BLOCK_START)
    if start < 0:
        return text
    end = text.find("</script>", start)
    if end < 0:
        return text
    return text[:start].rstrip() + "\n" + text[end + len("</script>") :].lstrip()


def _read_utf8(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def main() -> int:
    args = build_parser().parse_args()
    count = patch_sample_root(
        args.sample_root,
        sample_id_prefixes=list(args.sample_id_prefix),
        backup_root=args.backup_root,
        write=bool(args.write),
    )
    action = "patched" if args.write else "planned"
    print(f"[patch_e1_whatsapp_accessibility] {action} files={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
