from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from scripts.import_dataset_bundle import main as import_bundle_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import a dataset sample bundle into the database.")
    parser.add_argument(
        "--sample-root",
        type=Path,
        required=True,
        help="Root directory containing dataset samples.",
    )
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=BACKEND_ROOT / "dataset_metadata",
        help="Root directory containing datasets_demo metadata JSON files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the demo metadata and samples without writing to the database.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    forwarded_args = [
        "--sample-root",
        str(args.sample_root.resolve()),
        "--registry-root",
        str(args.registry_root.resolve()),
    ]
    if args.dry_run:
        forwarded_args.append("--dry-run")
    return import_bundle_main(forwarded_args)


if __name__ == "__main__":
    raise SystemExit(main())
