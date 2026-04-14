from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.datasets.metadata_registry import apply_metadata_bundle, load_metadata_bundle
from app.shared.config import settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import dataset metadata JSON files into the database.")
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=BACKEND_ROOT / "dataset_metadata",
        help="Root directory for registry/display_meta JSON files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate metadata files and print counts without writing to the database.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bundle = load_metadata_bundle(args.registry_root.resolve())
    print(
        "[import_dataset_metadata] validated "
        f"sources={len(bundle.dataset_sources)} "
        f"delivery_types={len(bundle.attack_delivery_types)} "
        f"asset_types={len(bundle.asset_types)} "
        f"categories={len(bundle.risk_categories)} "
        f"subtypes={len(bundle.risk_subtypes)} "
        f"display_meta={len(bundle.display_meta_by_code)}"
    )
    if args.dry_run:
        return 0

    engine = create_engine(settings.SYNC_DATABASE_URL, future=True)
    session_factory = sessionmaker(bind=engine, future=True)
    try:
        with session_factory() as session:
            result = apply_metadata_bundle(session, bundle)
            session.commit()
    finally:
        engine.dispose()

    print(
        "[import_dataset_metadata] imported "
        f"sources(created={result.created_sources}, updated={result.updated_sources}) "
        f"delivery_types(created={result.created_delivery_types}, updated={result.updated_delivery_types}) "
        f"asset_types(created={result.created_asset_types}, updated={result.updated_asset_types}) "
        f"categories(created={result.created_categories}, updated={result.updated_categories}) "
        f"subtypes(created={result.created_subtypes}, updated={result.updated_subtypes}) "
        f"display_meta(created={result.created_display_meta}, updated={result.updated_display_meta})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
