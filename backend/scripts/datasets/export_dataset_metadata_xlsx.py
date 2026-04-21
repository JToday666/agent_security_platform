"""把数据集元数据 JSON 导出为可编辑的 XLSX 工作簿。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允许通过 `python scripts/...` 直接执行时正确导入 backend 包内模块。
_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.modules.datasets.metadata_registry import load_metadata_bundle
from app.modules.datasets.metadata_workbook import export_metadata_workbook
from scripts._common import DATASET_METADATA_ROOT, DATASET_METADATA_WORKBOOK


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="Export dataset metadata JSON files to an editable XLSX workbook.")
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=DATASET_METADATA_ROOT,
        help="Root directory for registry/display_meta JSON files.",
    )
    parser.add_argument(
        "--xlsx",
        type=Path,
        default=DATASET_METADATA_WORKBOOK,
        help="Output workbook path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """加载元数据 bundle，并导出成 workbook 文件。"""
    args = build_parser().parse_args(argv)
    bundle = load_metadata_bundle(args.registry_root.resolve())
    export_metadata_workbook(bundle, args.xlsx.resolve())
    print(f"[export_dataset_metadata_xlsx] wrote workbook={args.xlsx.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
