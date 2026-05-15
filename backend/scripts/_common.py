"""脚本共用的路径常量与同步数据库会话工具。"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
BACKEND_CWD = str(BACKEND_ROOT)


def ensure_backend_root_on_path() -> None:
    """确保脚本可以直接导入 backend 下的 `app` 包。"""
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))


ensure_backend_root_on_path()

from app.platform.config import settings

DATA_ROOT = settings.dataset_root
DATASET_METADATA_ROOT = settings.dataset_metadata_root


def build_sync_engine() -> Engine:
    """创建供一次性脚本使用的同步数据库引擎。"""
    return create_engine(settings.SYNC_DATABASE_URL, future=True)


def build_sync_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """返回绑定同步引擎的 Session 工厂。"""
    return sessionmaker(bind=engine or build_sync_engine(), future=True)


@contextmanager
def sync_session_scope() -> Iterator[Session]:
    """提供自动释放引擎资源的同步 Session 上下文。"""
    engine = build_sync_engine()
    session_factory = build_sync_session_factory(engine)
    try:
        with session_factory() as session:
            yield session
    finally:
        engine.dispose()
