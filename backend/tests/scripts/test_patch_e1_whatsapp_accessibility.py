from __future__ import annotations

from pathlib import Path

from tests.helpers.scripts import load_module_from_path


def _load_module(backend_root: Path):
    return load_module_from_path(
        "patch_e1_whatsapp_accessibility_under_test",
        backend_root / "scripts" / "datasets" / "patch_e1_whatsapp_accessibility.py",
    )


def _whatsapp_html() -> str:
    return """
<!doctype html>
<html><body>
<input type="text" id="searchInput" data-pw="search-input" placeholder="Search contacts...">
<ul class="user-list" id="userList"></ul>
<span class="user-name" id="chatHeaderName" data-pw="chat-header-name">Select a user to start chatting</span>
<div class="chat-messages" id="chatMessages" data-pw="chat-messages"></div>
<input type="text" id="messageInput" data-pw="message-input" placeholder="Type a message...">
<button id="sendButton" data-pw="send-button">Send</button>
<script>
const users = [
  { id: 4, name: 'Julia', avatar: './images/julia-avatar.png', status: 'Online' }
];
function loadUsers() {
  userList.innerHTML = '';
  users.forEach(user => {
    const li = document.createElement('li');
    li.setAttribute('data-userid', user.id);
    const nameSpan = document.createElement('span');
    nameSpan.classList.add('name');
    nameSpan.textContent = user.name;
    li.appendChild(nameSpan);
    userList.appendChild(li);
  });
}
loadUsers();
userList.addEventListener('click', () => {});
</script>
</body></html>
"""


def test_patch_html_text_adds_stable_contact_and_control_semantics(
    backend_root: Path,
) -> None:
    module = _load_module(backend_root)

    updated = module.patch_html_text(_whatsapp_html())

    assert "e1-whatsapp-accessibility-patch-v2" in updated
    assert 'id="e1-whatsapp-accessibility-patch"' in updated
    assert "Open chat with " in updated
    assert "chat-contact-" in updated
    assert "messageInput.focus" not in updated
    assert "whatsapp_chat_selected" in updated
    assert "MutationObserver" in updated
    assert "Search WhatsApp contacts" in updated
    assert "Type WhatsApp message" in updated
    assert "Send WhatsApp message" in updated
    assert module.patch_html_text(updated) == updated


def test_patch_html_text_upgrades_focus_behavior_patch(backend_root: Path) -> None:
    module = _load_module(backend_root)
    html = _whatsapp_html().replace(
        "</body>",
        """
<script id="e1-whatsapp-accessibility-patch">
(function() {
  var PATCH_VERSION = 'e1-whatsapp-accessibility-patch-v1';
  function focusMessageInput() {
    var messageInput = document.getElementById('messageInput');
    messageInput.focus();
  }
})();
</script>
</body>
""",
    )

    updated = module.patch_html_text(html)

    assert "e1-whatsapp-accessibility-patch-v2" in updated
    assert "e1-whatsapp-accessibility-patch-v1" not in updated
    assert "messageInput.focus" not in updated
    assert updated.count('id="e1-whatsapp-accessibility-patch"') == 1


def test_patch_html_text_skips_non_whatsapp_page(backend_root: Path) -> None:
    module = _load_module(backend_root)
    html = "<html><body><input id='messageInput'><button id='sendButton'>Send</button></body></html>"

    assert module.patch_html_text(html) == html


def test_patch_sample_root_limits_to_e1_whatsapp_pages(
    tmp_path: Path,
    backend_root: Path,
) -> None:
    module = _load_module(backend_root)
    root = tmp_path / "datasets"
    e1_whatsapp = (
        root
        / "05_Fraud_Impersonation_and_Social_Engineering"
        / "E1_Phishing_and_Credential_Theft"
        / "Browser-art_E1_5"
        / "whatsapp"
        / "index.html"
    )
    e1_email = e1_whatsapp.parents[1] / "Browser-art_E1_1" / "email" / "index.html"
    f1_whatsapp = (
        root
        / "06_Content_and_Societal_Harm"
        / "F1_Harassment_and_Bullying"
        / "Browser-art_F1_1"
        / "whatsapp"
        / "index.html"
    )
    for path in (e1_whatsapp, e1_email, f1_whatsapp):
        path.parent.mkdir(parents=True, exist_ok=True)
    e1_whatsapp.write_text(_whatsapp_html(), encoding="utf-8")
    e1_email.write_text(_whatsapp_html(), encoding="utf-8")
    f1_whatsapp.write_text(_whatsapp_html(), encoding="utf-8")

    assert (
        module.patch_sample_root(
            root,
            sample_id_prefixes=["Browser-art_E1_"],
            backup_root=None,
            write=True,
        )
        == 1
    )
    assert "e1-whatsapp-accessibility-patch" in e1_whatsapp.read_text(
        encoding="utf-8"
    )
    assert "e1-whatsapp-accessibility-patch" not in e1_email.read_text(
        encoding="utf-8"
    )
    assert "e1-whatsapp-accessibility-patch" not in f1_whatsapp.read_text(
        encoding="utf-8"
    )
