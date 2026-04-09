from app.shared.config import settings


def ensure_runtime_dirs() -> None:
    for path in (
        settings.runtime_root,
        settings.uploads_root,
        settings.avatars_root,
        settings.credential_storage_dir,
        settings.worker_workdir_root,
    ):
        path.mkdir(parents=True, exist_ok=True)
