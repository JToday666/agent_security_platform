from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.datasets.metadata_registry import build_metadata_bundle_from_database, write_metadata_bundle
from app.shared.config import settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap dataset metadata JSON files from the database.")
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=BACKEND_ROOT / "dataset_metadata",
        help="Root directory for registry/display_meta JSON files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = create_engine(settings.SYNC_DATABASE_URL, future=True)
    session_factory = sessionmaker(bind=engine, future=True)
    try:
        with session_factory() as session:
            bundle = build_metadata_bundle_from_database(session)
        write_metadata_bundle(args.registry_root.resolve(), bundle)
    finally:
        engine.dispose()

    print(
        "[bootstrap_dataset_metadata_from_db] wrote "
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
