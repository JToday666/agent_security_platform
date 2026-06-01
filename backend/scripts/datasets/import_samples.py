"""把样本目录中的 task 数据导入数据库。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.modules.datasets.ingestion.samples import (
    apply_sample_import_plan,
    build_sample_import_plan,
)
from scripts._common import sync_session_scope


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Import dataset samples into the database."
    )
    parser.add_argument(
        "--sample-root",
        type=Path,
        required=True,
        help="Root directory containing dataset samples.",
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
        help="Validate sample metadata and print counts without writing to the database.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """解析样本目录，先构建导入计划，再按需写库。"""
    args = build_parser().parse_args(argv)
    plan = build_sample_import_plan(args.sample_root.resolve(), mode=args.mode)
    print(
        f"[import_samples] validated samples={len(plan.samples)} from {args.sample_root.resolve()}"
    )
    if args.dry_run:
        return 0

    with sync_session_scope() as session:
        result = apply_sample_import_plan(session, plan)
        session.commit()

    print(
        "[import_samples] imported "
        f"samples(created={result.created_samples}, updated={result.updated_samples}) "
        f"oracles(created={result.created_oracles}, updated={result.updated_oracles}, "
        f"deactivated={result.deactivated_oracles})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
