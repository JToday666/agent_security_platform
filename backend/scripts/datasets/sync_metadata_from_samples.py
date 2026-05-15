"""根据样本目录补齐或更新 registry 元数据骨架。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.modules.datasets.ingestion.metadata import sync_metadata_from_samples
from scripts._common import DATASET_METADATA_ROOT


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Sync registry JSON skeletons from sample directories."
    )
    parser.add_argument(
        "--sample-root",
        type=Path,
        required=True,
        help="Root directory containing dataset samples.",
    )
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=DATASET_METADATA_ROOT,
        help="Root directory for registry/display_meta JSON files.",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "legacy", "standard"],
        default="auto",
        help="Sample metadata detection mode.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """扫描样本目录并同步生成 registry/display_meta 基础文件。"""
    args = build_parser().parse_args(argv)
    bundle = sync_metadata_from_samples(
        args.sample_root.resolve(), args.registry_root.resolve(), mode=args.mode
    )
    print(
        "[sync_metadata_from_samples] synced "
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
