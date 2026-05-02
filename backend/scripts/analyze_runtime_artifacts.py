"""Analyze one runtime run directory and write analysis_result.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.worker.analysis.service import analyze_runtime_artifacts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze runtime artifacts for one sample execution.")
    parser.add_argument("--task", type=Path, required=True, help="Path to the sample task.json.")
    parser.add_argument("--run-dir", type=Path, required=True, help="Path to agent_runtime/runs/<run_id>.")
    parser.add_argument("--output", type=Path, required=True, help="Output path for analysis_result.json.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = analyze_runtime_artifacts(
        task_path=args.task,
        run_dir=args.run_dir,
        output_path=args.output,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
