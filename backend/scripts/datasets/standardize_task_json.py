"""将样本根 task.json 从 legacy 格式就地标准化。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.modules.datasets.ingestion.errors import ImportValidationError
from app.modules.datasets.ingestion.samples import (
    detect_metadata_format,
    normalize_sample_metadata_file,
    planned_sample_to_standard_task_payload,
)
from scripts._common import DATA_ROOT


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数。"""
    parser = argparse.ArgumentParser(
        description="Standardize legacy sample task.json files in-place."
    )
    parser.add_argument(
        "--sample-root",
        type=Path,
        default=DATA_ROOT,
        help="Root directory containing data/datasets style sample folders.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write standardized task.json files. Without this flag the script only reports planned changes.",
    )
    return parser


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def standardize_task_json(sample_root: Path, *, write: bool) -> tuple[int, int, int]:
    """标准化 legacy task.json，返回 samples/changed/errors 统计。"""
    root = sample_root.resolve()
    if not root.exists():
        raise ImportValidationError(f"样本根目录不存在: {root}")

    sample_count = 0
    changed_count = 0
    error_count = 0
    for task_path in sorted(root.rglob("task.json")):
        if "saved_logs" in task_path.parts:
            continue
        sample_count += 1
        try:
            payload = json.loads(task_path.read_text(encoding="utf-8"))
            fmt = detect_metadata_format(payload)
            if fmt == "standard":
                continue
            if fmt != "legacy":
                raise ImportValidationError(f"{task_path}: 不支持的 task.json 格式")
            planned_sample = normalize_sample_metadata_file(task_path, root, "legacy")
            next_text = _canonical_json(
                planned_sample_to_standard_task_payload(planned_sample)
            )
            if task_path.read_text(encoding="utf-8") == next_text:
                continue
            changed_count += 1
            if write:
                task_path.write_text(next_text, encoding="utf-8")
        except Exception as exc:
            error_count += 1
            print(
                f"[standardize_task_json] error path={task_path} message={exc}",
                file=sys.stderr,
            )
    return sample_count, changed_count, error_count


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sample_count, changed_count, error_count = standardize_task_json(
        args.sample_root, write=args.write
    )
    mode = "write" if args.write else "dry-run"
    print(
        "[standardize_task_json] "
        f"mode={mode} samples={sample_count} changed={changed_count} errors={error_count}"
    )
    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
