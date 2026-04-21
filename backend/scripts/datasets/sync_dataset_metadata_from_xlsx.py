"""把工作簿中的编辑结果同步回数据集元数据 JSON。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允许通过 `python scripts/...` 直接执行时正确导入 backend 包内模块。
_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.modules.datasets.metadata_workbook import sync_metadata_from_workbook
from scripts._common import DATASET_METADATA_ROOT, DATASET_METADATA_WORKBOOK


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="Sync dataset metadata JSON files from an XLSX workbook.")
    parser.add_argument(
        "--xlsx",
        type=Path,
        default=DATASET_METADATA_WORKBOOK,
        help="Workbook path.",
    )
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=DATASET_METADATA_ROOT,
        help="Root directory for registry/display_meta JSON files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """读取 workbook 并回写 registry/display_meta JSON 文件。"""
    args = build_parser().parse_args(argv)
    bundle = sync_metadata_from_workbook(args.xlsx.resolve(), args.registry_root.resolve())
    print(
        "[sync_dataset_metadata_from_xlsx] synced "
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
