from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app
from app.shared.config import settings
from tests.helpers.api_db import ApiDbHelper
from tests.helpers.dataset_bundle import SampleBundleInfo, write_repo_like_sample_bundle


@pytest.fixture(scope="session")
def backend_root() -> Path:
    return BACKEND_ROOT


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def sync_engine():
    engine = create_engine(settings.SYNC_DATABASE_URL, future=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def session_factory(sync_engine):
    return sessionmaker(bind=sync_engine, future=True)


@pytest.fixture
def db_session(sync_engine) -> Session:
    connection = sync_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, future=True)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def api_db_helper(session_factory) -> ApiDbHelper:
    helper = ApiDbHelper(session_factory=session_factory, prefix=f"pytest_{uuid4().hex[:8]}")
    try:
        yield helper
    finally:
        helper.cleanup()


@pytest.fixture
def repo_sample_bundle(tmp_path: Path) -> SampleBundleInfo:
    return write_repo_like_sample_bundle(tmp_path / "samples")
