"""把原始样本目录规整成标准化 task.json bundle。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.modules.datasets.ingestion.normalize import normalize_sample_bundle
from scripts._common import DATA_ROOT


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Normalize raw dataset samples into a standard task.json bundle."
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        default=DATA_ROOT,
        help="Root directory containing raw dataset samples.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory for the normalized sample bundle.",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "legacy", "standard"],
        default="auto",
        help="Sample metadata detection mode.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate raw samples and report counts without writing the normalized bundle.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """对输入样本做标准化整理，并输出可继续导入的 bundle。"""
    args = build_parser().parse_args(argv)
    result = normalize_sample_bundle(
        input_root=args.input_root.resolve(),
        output_root=args.output_dir.resolve(),
        mode=args.mode,
        dry_run=args.dry_run,
    )
    if args.dry_run:
        print(
            "[normalize_samples] validated "
            f"samples={result.sample_count} input_root={result.input_root} output_dir={result.output_root}"
        )
        return 0

    print(
        "[normalize_samples] wrote "
        f"samples={result.sample_count} "
        f"task_json={result.written_task_count} "
        f"symlinks={result.symlinked_file_count} "
        f"output_dir={result.output_root}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
