"""根据 display_meta 明细生成聚合索引文件。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允许通过 `python scripts/...` 直接执行时正确导入 backend 包内模块。
_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.modules.datasets.metadata_registry import load_metadata_bundle, write_display_meta_index
from scripts._common import DATASET_METADATA_ROOT


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="Generate display_meta/index.json from dataset metadata JSON files.")
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=DATASET_METADATA_ROOT,
        help="Root directory for registry/display_meta JSON files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """重新生成 display_meta/index.json，便于前端批量读取。"""
    args = build_parser().parse_args(argv)
    bundle = load_metadata_bundle(args.registry_root.resolve())
    index_path = write_display_meta_index(args.registry_root.resolve(), bundle)
    print(
        "[generate_dataset_display_meta_index] wrote "
        f"index={index_path} entries={len(bundle.display_meta_by_code)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
