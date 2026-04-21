"""数据集导入顶层编排逻辑。"""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.modules.datasets.ingestion.metadata import (
    apply_metadata_bundle,
    build_metadata_bundle_from_samples,
    write_metadata_bundle,
)
from app.modules.datasets.ingestion.normalize import detect_sample_root_kind, normalize_sample_bundle
from app.modules.datasets.ingestion.samples import apply_sample_import_plan, build_sample_import_plan
from app.modules.datasets.ingestion.types import ImportPipelineResult
from app.shared.config import settings


@contextmanager
def sync_session_scope() -> Iterator[Session]:
    """提供供导入 pipeline 使用的同步会话。"""
    engine = create_engine(settings.SYNC_DATABASE_URL, future=True)
    session_factory = sessionmaker(bind=engine, future=True)
    try:
        with session_factory() as session:
            yield session
    finally:
        engine.dispose()


def run_import_pipeline(
    *,
    sample_root: Path,
    registry_root: Path,
    mode: str = "auto",
    dry_run: bool = False,
    workspace_dir: Path | None = None,
) -> ImportPipelineResult:
    """智能执行标准化、元数据同步与导入链路。"""
    source_root = sample_root.resolve()
    registry_root = registry_root.resolve()
    input_kind = detect_sample_root_kind(source_root, mode=mode)

    with ExitStack() as stack:
        effective_sample_root = source_root
        normalization_result = None

        if input_kind == "raw":
            if workspace_dir is None:
                workspace_root = Path(stack.enter_context(TemporaryDirectory(prefix="dataset_import_workspace_")))
            else:
                workspace_root = workspace_dir.resolve()
                workspace_root.mkdir(parents=True, exist_ok=True)
            normalized_root = workspace_root / "normalized_samples"
            normalization_result = normalize_sample_bundle(source_root, normalized_root, mode=mode, dry_run=False)
            effective_sample_root = normalization_result.output_root

        effective_mode = "standard" if input_kind == "raw" else mode
        sample_plan = build_sample_import_plan(effective_sample_root, mode=effective_mode)
        metadata_bundle = build_metadata_bundle_from_samples(effective_sample_root, registry_root, mode=effective_mode)

        metadata_result = None
        sample_result = None
        if not dry_run:
            write_metadata_bundle(registry_root, metadata_bundle)
            with sync_session_scope() as session:
                metadata_result = apply_metadata_bundle(session, metadata_bundle)
                sample_result = apply_sample_import_plan(session, sample_plan)
                session.commit()

        return ImportPipelineResult(
            input_kind=input_kind,
            sample_root=source_root,
            effective_sample_root=effective_sample_root,
            registry_root=registry_root,
            sample_plan=sample_plan,
            metadata_bundle=metadata_bundle,
            normalized=normalization_result is not None,
            normalization_result=normalization_result,
            metadata_result=metadata_result,
            sample_result=sample_result,
        )
