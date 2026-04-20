from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.datasets.importer import apply_sample_import_plan, build_sample_import_plan
from app.shared.config import settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import dataset samples into the database.")
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
    args = build_parser().parse_args(argv)
    plan = build_sample_import_plan(args.sample_root.resolve(), mode=args.mode)
    print(f"[import_dataset_samples] validated samples={len(plan.samples)} from {args.sample_root.resolve()}")
    if args.dry_run:
        return 0

    engine = create_engine(settings.SYNC_DATABASE_URL, future=True)
    session_factory = sessionmaker(bind=engine, future=True)
    try:
        with session_factory() as session:
            result = apply_sample_import_plan(session, plan)
            session.commit()
    finally:
        engine.dispose()

    print(
        "[import_dataset_samples] imported "
        f"samples(created={result.created_samples}, updated={result.updated_samples}) "
        f"oracles(created={result.created_oracles}, updated={result.updated_oracles})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
