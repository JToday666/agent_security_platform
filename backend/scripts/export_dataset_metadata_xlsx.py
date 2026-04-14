from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.datasets.metadata_registry import load_metadata_bundle
from app.modules.datasets.metadata_workbook import export_metadata_workbook


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export dataset metadata JSON files to an editable XLSX workbook.")
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=BACKEND_ROOT / "dataset_metadata",
        help="Root directory for registry/display_meta JSON files.",
    )
    parser.add_argument(
        "--xlsx",
        type=Path,
        default=BACKEND_ROOT / "dataset_metadata" / "workbook" / "dataset_registry.xlsx",
        help="Output workbook path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bundle = load_metadata_bundle(args.registry_root.resolve())
    export_metadata_workbook(bundle, args.xlsx.resolve())
    print(f"[export_dataset_metadata_xlsx] wrote workbook={args.xlsx.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
