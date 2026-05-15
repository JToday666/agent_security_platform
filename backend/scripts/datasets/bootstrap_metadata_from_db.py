"""从数据库反向导出数据集元数据 JSON 文件。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.modules.datasets.ingestion.metadata import (
    build_metadata_bundle_from_database,
    write_metadata_bundle,
)
from scripts._common import DATASET_METADATA_ROOT, sync_session_scope


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Bootstrap dataset metadata JSON files from the database."
    )
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=DATASET_METADATA_ROOT,
        help="Root directory for registry/display_meta JSON files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """读取数据库当前元数据并写回 registry/display_meta 文件。"""
    args = build_parser().parse_args(argv)
    with sync_session_scope() as session:
        bundle = build_metadata_bundle_from_database(session)
    write_metadata_bundle(args.registry_root.resolve(), bundle)

    print(
        "[bootstrap_metadata_from_db] wrote "
        f"sources={len(bundle.dataset_sources)} "
        f"delivery_types={len(bundle.attack_delivery_types)} "
        f"asset_types={len(bundle.asset_types)} "
        f"categories={len(bundle.risk_categories)} "
        f"subtypes={len(bundle.risk_subtypes)} "
        f"display_meta={len(bundle.display_meta_by_code)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
