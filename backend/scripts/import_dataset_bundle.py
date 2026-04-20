from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.modules.datasets.importer import ImportValidationError, build_sample_import_plan
from app.modules.datasets.metadata_registry import apply_metadata_bundle, load_metadata_bundle
from app.shared.config import settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import dataset metadata and samples as a single bundle.")
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
        help="Root directory for registry/display_meta JSON files.",
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
        help="Validate both metadata and samples without writing to the database.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bundle = load_metadata_bundle(args.registry_root.resolve())
    sample_plan = build_sample_import_plan(args.sample_root.resolve(), mode=args.mode)

    if args.dry_run:
        _validate_sample_plan_against_bundle(sample_plan, bundle)
        print(
            "[import_dataset_bundle] validated "
            f"metadata_sources={len(bundle.dataset_sources)} "
            f"metadata_subtypes={len(bundle.risk_subtypes)} "
            f"samples={len(sample_plan.samples)}"
        )
        return 0

    engine = create_engine(settings.SYNC_DATABASE_URL, future=True)
    session_factory = sessionmaker(bind=engine, future=True)
    try:
        with session_factory() as session:
            metadata_result = apply_metadata_bundle(session, bundle)
            from app.modules.datasets.importer import apply_sample_import_plan  # local import to keep script light

            sample_result = apply_sample_import_plan(session, sample_plan)
            session.commit()
    finally:
        engine.dispose()

    print(
        "[import_dataset_bundle] imported "
        f"metadata_subtypes(created={metadata_result.created_subtypes}, updated={metadata_result.updated_subtypes}) "
        f"samples(created={sample_result.created_samples}, updated={sample_result.updated_samples}) "
        f"oracles(created={sample_result.created_oracles}, updated={sample_result.updated_oracles})"
    )
    return 0


def _validate_sample_plan_against_bundle(sample_plan, bundle) -> None:
    source_codes = {item.code for item in bundle.dataset_sources}
    delivery_codes = {item.code for item in bundle.attack_delivery_types}
    asset_codes = {item.code for item in bundle.asset_types}
    category_codes = {item.code for item in bundle.risk_categories}
    subtype_to_category = {item.code: item.category_code for item in bundle.risk_subtypes}

    for sample in sample_plan.samples:
        if sample.dataset_source_code not in source_codes:
            raise ImportValidationError(f"{sample.metadata_path}: dataset_source_code={sample.dataset_source_code} 未在元数据中注册")
        if sample.attack_delivery_type_code not in delivery_codes:
            raise ImportValidationError(
                f"{sample.metadata_path}: attack_delivery_type_code={sample.attack_delivery_type_code} 未在元数据中注册"
            )
        if sample.risk_category_code not in category_codes:
            raise ImportValidationError(f"{sample.metadata_path}: risk_category_code={sample.risk_category_code} 未在元数据中注册")
        if sample.risk_subtype_code not in subtype_to_category:
            raise ImportValidationError(f"{sample.metadata_path}: risk_subtype_code={sample.risk_subtype_code} 未在元数据中注册")
        if subtype_to_category[sample.risk_subtype_code] != sample.risk_category_code:
            raise ImportValidationError(
                f"{sample.metadata_path}: risk_subtype_code={sample.risk_subtype_code} 与 risk_category_code={sample.risk_category_code} 不匹配"
            )
        if sample.asset_type_code and sample.asset_type_code not in asset_codes:
            raise ImportValidationError(f"{sample.metadata_path}: asset_type_code={sample.asset_type_code} 未在元数据中注册")


if __name__ == "__main__":
    raise SystemExit(main())
