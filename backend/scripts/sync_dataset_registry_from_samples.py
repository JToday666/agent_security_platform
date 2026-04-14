from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.datasets.metadata_registry import sync_registry_from_samples


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync registry JSON skeletons from sample directories.")
    parser.add_argument(
        "--sample-root",
        type=Path,
        default=BACKEND_ROOT / "datasets_demo",
        help="Root directory containing dataset samples.",
    )
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=BACKEND_ROOT / "dataset_metadata",
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
    args = build_parser().parse_args(argv)
    bundle = sync_registry_from_samples(args.sample_root.resolve(), args.registry_root.resolve(), mode=args.mode)
    print(
        "[sync_dataset_registry_from_samples] synced "
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
