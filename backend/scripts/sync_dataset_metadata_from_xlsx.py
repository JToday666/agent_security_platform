from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.datasets.metadata_workbook import sync_metadata_from_workbook


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync dataset metadata JSON files from an XLSX workbook.")
    parser.add_argument(
        "--xlsx",
        type=Path,
        default=BACKEND_ROOT / "dataset_metadata" / "workbook" / "dataset_registry.xlsx",
        help="Workbook path.",
    )
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=BACKEND_ROOT / "dataset_metadata",
        help="Root directory for registry/display_meta JSON files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
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
