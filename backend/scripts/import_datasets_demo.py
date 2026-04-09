from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.datasets.importer import ImportValidationError, apply_import_plan, build_import_plan
from app.shared.config import settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import dataset demo samples into the database.")
    parser.add_argument(
        "--sample-root",
        type=Path,
        default=BACKEND_ROOT / "datasets_demo",
        help="Root directory containing datasets_demo samples.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the import plan without writing to the database.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sample_root = args.sample_root.resolve()

    try:
        plan = build_import_plan(sample_root)
    except ImportValidationError as exc:
        print(f"[import_datasets_demo] validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"[import_datasets_demo] validated {len(plan.samples)} samples from {sample_root}")
    if args.dry_run:
        return 0

    engine = create_engine(settings.SYNC_DATABASE_URL, future=True)
    session_factory = sessionmaker(bind=engine, future=True)
    try:
        with session_factory() as session:
            result = apply_import_plan(session, plan)
            session.commit()
    except Exception:
        engine.dispose()
        raise

    engine.dispose()
    print(
        "[import_datasets_demo] imported "
        f"samples(created={result.created_samples}, updated={result.updated_samples}) "
        f"oracles(created={result.created_oracles}, updated={result.updated_oracles})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
