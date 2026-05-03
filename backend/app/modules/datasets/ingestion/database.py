"""Synchronous database boundary for dataset ingestion jobs."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.modules.datasets.ingestion.metadata import apply_metadata_bundle
from app.modules.datasets.ingestion.samples import apply_sample_import_plan
from app.modules.datasets.ingestion.types import MetadataBundle, MetadataImportResult, SampleImportPlan, SampleImportResult
from app.platform.config import settings


@contextmanager
def sync_session_scope() -> Iterator[Session]:
    """Provide a short-lived synchronous session for ingestion scripts."""
    engine = create_engine(settings.SYNC_DATABASE_URL, future=True)
    session_factory = sessionmaker(bind=engine, future=True)
    try:
        with session_factory() as session:
            yield session
    finally:
        engine.dispose()


def apply_ingestion_bundle(
    *,
    metadata_bundle: MetadataBundle,
    sample_plan: SampleImportPlan,
) -> tuple[MetadataImportResult, SampleImportResult]:
    """Apply metadata and sample changes within one committed transaction."""
    with sync_session_scope() as session:
        metadata_result = apply_metadata_bundle(session, metadata_bundle)
        sample_result = apply_sample_import_plan(session, sample_plan)
        session.commit()
    return metadata_result, sample_result

