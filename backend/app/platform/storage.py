"""Storage factories and path accessors for application services."""

from pathlib import Path

from app.platform.config import settings
from app.platform.credentials import CredentialStore, FileCredentialStore


def default_credential_store() -> CredentialStore:
    """Build the default file-backed credential store."""
    return FileCredentialStore(settings.credential_storage_dir, settings.SECRET_KEY)


def default_avatars_root() -> Path:
    """Return the configured avatar storage directory."""
    return settings.avatars_root
