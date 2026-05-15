"""把 registry/display_meta JSON 元数据导入数据库。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.modules.datasets.ingestion.metadata import (
    apply_metadata_bundle,
    load_metadata_bundle,
)
from scripts._common import DATASET_METADATA_ROOT, sync_session_scope


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Import dataset metadata JSON files into the database."
    )
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=DATASET_METADATA_ROOT,
        help="Root directory for registry/display_meta JSON files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate metadata files and print counts without writing to the database.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """加载元数据 bundle，先校验，再按需写库。"""
    args = build_parser().parse_args(argv)
    bundle = load_metadata_bundle(args.registry_root.resolve())
    print(
        "[import_metadata] validated "
        f"sources={len(bundle.dataset_sources)} "
        f"delivery_types={len(bundle.attack_delivery_types)} "
        f"asset_types={len(bundle.asset_types)} "
        f"categories={len(bundle.risk_categories)} "
        f"subtypes={len(bundle.risk_subtypes)} "
        f"display_meta={len(bundle.display_meta_by_code)}"
    )
    if args.dry_run:
        return 0

    with sync_session_scope() as session:
        result = apply_metadata_bundle(session, bundle)
        session.commit()

    print(
        "[import_metadata] imported "
        f"sources(created={result.created_sources}, updated={result.updated_sources}) "
        f"delivery_types(created={result.created_delivery_types}, updated={result.updated_delivery_types}) "
        f"asset_types(created={result.created_asset_types}, updated={result.updated_asset_types}) "
        f"categories(created={result.created_categories}, updated={result.updated_categories}) "
        f"subtypes(created={result.created_subtypes}, updated={result.updated_subtypes}) "
        f"display_meta(created={result.created_display_meta}, updated={result.updated_display_meta})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
