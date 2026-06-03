"""智能执行标准化、元数据同步与数据库导入。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[1]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.modules.datasets.ingestion.pipeline import run_import_pipeline
from app.platform.config import settings


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Normalize, sync metadata, and import datasets through the full pipeline."
    )
    parser.add_argument(
        "--sample-root",
        type=Path,
        default=None,
        help=(
            "Root directory containing raw or standard dataset samples. "
            "Defaults to DATASET_ROOT_DIR/settings.dataset_root."
        ),
    )
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=None,
        help=(
            "Root directory for registry/display_meta JSON files. "
            "Defaults to DATASET_METADATA_ROOT_DIR/settings.dataset_metadata_root."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "legacy", "standard"],
        default="auto",
        help="Sample metadata detection mode.",
    )
    parser.add_argument(
        "--workspace-dir",
        type=Path,
        default=None,
        help="Workspace directory used for normalized intermediate files when raw samples are detected.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the full pipeline without writing to the database.",
    )
    return parser


def _resolve_roots(args: argparse.Namespace) -> tuple[Path, Path]:
    """Resolve CLI roots, falling back to configured dataset roots."""
    sample_root = args.sample_root or settings.dataset_root
    registry_root = args.registry_root or settings.dataset_metadata_root
    return sample_root.resolve(), registry_root.resolve()


def main(argv: list[str] | None = None) -> int:
    """执行一键导入 pipeline。"""
    args = build_parser().parse_args(argv)
    sample_root, registry_root = _resolve_roots(args)
    result = run_import_pipeline(
        sample_root=sample_root,
        registry_root=registry_root,
        mode=args.mode,
        dry_run=args.dry_run,
        workspace_dir=args.workspace_dir.resolve() if args.workspace_dir else None,
    )

    normalized = "yes" if result.normalized else "no"
    if args.dry_run:
        print(
            "[import_datasets] planned "
            f"input_kind={result.input_kind} "
            f"normalized={normalized} "
            f"samples={result.sample_count} "
            f"metadata_scenarios={len(result.metadata_bundle.attack_scenarios)} "
            f"metadata_sources={len(result.metadata_bundle.dataset_sources)} "
            f"metadata_subtypes={len(result.metadata_bundle.risk_subtypes)}"
        )
        return 0

    assert result.metadata_result is not None
    assert result.sample_result is not None
    print(
        "[import_datasets] imported "
        f"input_kind={result.input_kind} "
        f"normalized={normalized} "
        f"samples={result.sample_count} "
        f"metadata_scenarios(created={result.metadata_result.created_attack_scenarios}, updated={result.metadata_result.updated_attack_scenarios}) "
        f"metadata_subtypes(created={result.metadata_result.created_subtypes}, updated={result.metadata_result.updated_subtypes}) "
        f"display_meta(created={result.metadata_result.created_display_meta}, updated={result.metadata_result.updated_display_meta}) "
        f"sample_rows(created={result.sample_result.created_samples}, updated={result.sample_result.updated_samples}) "
        f"oracles(created={result.sample_result.created_oracles}, updated={result.sample_result.updated_oracles}, "
        f"deactivated={result.sample_result.deactivated_oracles})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
