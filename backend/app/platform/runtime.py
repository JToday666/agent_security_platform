"""运行时目录初始化工具。"""

from app.platform.config import settings


def ensure_runtime_dirs() -> None:
    """确保服务运行所需目录存在。"""
    for path in (
        settings.runtime_root,
        settings.uploads_root,
        settings.avatars_root,
        settings.credential_storage_dir,
        settings.worker_workdir_root,
    ):
        path.mkdir(parents=True, exist_ok=True)
